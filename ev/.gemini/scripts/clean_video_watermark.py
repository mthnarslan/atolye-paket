"""
clean_video_watermark.py - 2-Aşamalı Ultra-Hafif ve Pürüzsüz Filigran/Logo Temizleme Betiği
-----------------------------------------------------------------------------------------
Aşama 1 (Hedefleme): Standart 'delogo' gibi dikdörtgeni körü körüne bulandırmak yerine,
                      sadece logo/yazı siluetini sub-pixel düzeyde izole eder.
Aşama 2 (Temizleme): 
  - Mod A (Temporal Patch): Statik/tripod çekimlerde temiz referans karesinden dokuyu alıp
    Gaussian feathered alpha maskesiyle yağ gibi eritir (0 CPU/GPU yükü, 0 beyaz leke).
  - Mod B (Stroke Inpaint): Dinamik sahnelerde sadece izole edilen harf siluetini Navier-Stokes / Telea
    ile dokuya yedirir (kutucuk oluşturmaz, beyaz silik iz bırakmaz).
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import cv2
import numpy as np

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def build_feathered_mask(height, width, pad_top=8, pad_bottom=8, pad_left=8, pad_right=14, blur_k=11):
    """Sınır geçişlerini görünmez kılan yumuşak Gaussian alpha maskesi üretir."""
    alpha = np.ones((height, width), dtype=np.float32)
    if pad_top > 0:
        alpha[:pad_top, :] *= np.linspace(0, 1, pad_top)[:, None]
    if pad_bottom > 0:
        alpha[-pad_bottom:, :] *= np.linspace(1, 0, pad_bottom)[:, None]
    if pad_left > 0:
        alpha[:, :pad_left] *= np.linspace(0, 1, pad_left)[None, :]
    if pad_right > 0:
        alpha[:, -pad_right:] *= np.linspace(1, 0, pad_right)[None, :]
    
    blur_k = blur_k if blur_k % 2 == 1 else blur_k + 1
    alpha = cv2.GaussianBlur(alpha, (blur_k, blur_k), 3)
    return alpha[:, :, None]


def clean_watermark(input_path, output_path=None, roi=(710, 845, 10, 880),
                    mode="patch", ref_frame_idx=5, threshold=240, crf=18):
    input_file = Path(input_path)
    if not input_file.is_file():
        print(f"[-] Hata: Girdi videosu bulunamadı: {input_file}")
        return False

    if output_path is None:
        output_file = input_file.parent / f"{input_file.stem}_clean.mp4"
    else:
        output_file = Path(output_path)

    temp_video = input_file.parent / f"temp_{os.getpid()}_no_audio.mp4"

    cap = cv2.VideoCapture(str(input_file))
    if not cap.isOpened():
        print(f"[-] Hata: Video açılamadı: {input_file}")
        return False

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    y1, y2, x1, x2 = roi
    # Sınır kontrolü
    y1, y2 = max(0, y1), min(height, y2)
    x1, x2 = max(0, x1), min(width, x2)
    roi_h, roi_w = y2 - y1, x2 - x1

    print(f"[+] Video Açıldı: {width}x{height} @ {fps:.2f} fps | {total_frames} kare")
    print(f"[+] Aşama 1: Hedef ROI: y:[{y1}:{y2}], x:[{x1}:{x2}] (Boyut: {roi_w}x{roi_h})")
    print(f"[+] Aşama 2: Temizleme Modu: {mode.upper()}")

    # Mod A Hazırlığı (Temporal Patch)
    clean_patch_f = None
    alpha_mask = None
    if mode == "patch":
        cap.set(cv2.CAP_PROP_POS_FRAMES, ref_frame_idx)
        ret, ref_frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, ref_frame = cap.read()
        
        clean_patch = ref_frame[y1:y2, x1:x2].copy()
        clean_patch_f = clean_patch.astype(np.float32)
        alpha_mask = build_feathered_mask(roi_h, roi_w)
        print(f"[+] Referans dokusu Kare #{ref_frame_idx} üzerinden örneklendi.")

    # Mod B Hazırlığı (Morfolojik Elips Çekirdek)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(temp_video), fourcc, fps, (width, height))

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        roi_crop = frame[y1:y2, x1:x2]

        if mode == "patch":
            # Dinamik Pozlama Dengeleme (Gain Matching):
            # Referans karesi ile mevcut kare arasındaki ışık farkını çevre piksel bandından hesapla
            sample_y1 = max(0, y1 - 40)
            sample_y2 = y1
            ref_surround = ref_frame[sample_y1:sample_y2, x1:x2].astype(np.float32)
            cur_surround = frame[sample_y1:sample_y2, x1:x2].astype(np.float32)
            
            mean_ref = np.mean(ref_surround)
            mean_cur = np.mean(cur_surround)
            gain = (mean_cur / (mean_ref + 1e-4)) if mean_ref > 5 else 1.0
            gain = np.clip(gain, 0.2, 5.0)

            # Statik / Feathered Blend: 0 CPU yükü, 0 beyaz leke
            adjusted_patch = clean_patch_f * gain
            roi_f = roi_crop.astype(np.float32)
            blended = adjusted_patch * alpha_mask + roi_f * (1.0 - alpha_mask)
            frame[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)

        elif mode == "inpaint":
            # Dinamik / Harf Silueti Temelli Inpainting
            gray = cv2.cvtColor(roi_crop, cv2.COLOR_BGR2GRAY)
            mask = (gray >= threshold).astype(np.uint8) * 255
            # Sadece harf gövdesini ve kenar anti-alias izlerini kapsayacak kadar (1-2 px) genişlet
            dilated_mask = cv2.dilate(mask, kernel, iterations=1)
            
            if cv2.countNonZero(dilated_mask) > 0:
                cleaned_roi = cv2.inpaint(roi_crop, dilated_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
                frame[y1:y2, x1:x2] = cleaned_roi

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    print(f"[+] Görsel onarım tamamlandı: {frame_idx} kare işlendi.")

    # Aşama 3: Ses Entegrasyonu & 1080p CRF 18 Render
    print("[+] Orijinal ses kanalı kayıpsız birleştiriliyor...")
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(temp_video),
        "-i", str(input_file),
        "-c:v", "libx264", "-crf", str(crf), "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-shortest",
        str(output_file)
    ]
    res = subprocess.run(cmd)

    if temp_video.is_file():
        temp_video.unlink()

    if res.returncode == 0 and output_file.is_file():
        print(f"[OK] BASARILI: Temiz nihai video kaydedildi: {output_file}")
        return True
    else:
        print("[-] FFmpeg render hatasi!")
        return False


def main():
    parser = argparse.ArgumentParser(description="2-Stage Clean Video Watermark Remover")
    parser.add_argument("--input", "-i", type=str, default=r"C:\Users\meteh\CodexOutputs\TOPIC_2\03_materials\shots\0055\repair_3\scene.mp4",
                        help="Girdi videosu yolu")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Çıktı videosu yolu (boş bırakılırsa <ad>_clean.mp4 olur)")
    parser.add_argument("--roi", nargs=4, type=int, default=[710, 845, 10, 880],
                        metavar=("Y1", "Y2", "X1", "X2"), help="Hedef koordinatlar: Y1 Y2 X1 X2")
    parser.add_argument("--mode", "-m", choices=["patch", "inpaint"], default="patch",
                        help="Temizleme modu: 'patch' (tripod/statik) veya 'inpaint' (dinamik)")
    parser.add_argument("--ref-frame", type=int, default=5,
                        help="Patch modu için temiz referans karesi indeksi (varsayılan: 5)")
    parser.add_argument("--thresh", type=int, default=240,
                        help="Inpaint modu için harf beyazlık eşiği (0-255, varsayılan: 240)")
    parser.add_argument("--crf", type=int, default=18,
                        help="FFmpeg H.264 CRF değeri (varsayılan: 18)")

    args = parser.parse_args()
    success = clean_watermark(
        input_path=args.input,
        output_path=args.output,
        roi=tuple(args.roi),
        mode=args.mode,
        ref_frame_idx=args.ref_frame,
        threshold=args.thresh,
        crf=args.crf
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
