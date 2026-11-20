"""
HYPERFRAMES & OVERLAY HARDENER - PHYSICAL QA AUDITOR (BLUE TEAM)
Measures: Alpha Translucency, Pixel Area, WCAG 2.1 AA Contrast, Laplacian Sharpness, Title Safe Margins.
Enforces PIL Ban and HyperFrames (HTML+GSAP) standards.
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
import cv2
import numpy as np

def srgb_to_linear(c):
    """Convert sRGB array [0..255] to linear luminance values [0..1] (IEC 61966-2-1)."""
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def calculate_relative_luminance(rgb_array):
    """Calculate WCAG 2.1 relative luminance: L = 0.2126*R + 0.7152*G + 0.0722*B."""
    r_lin = srgb_to_linear(rgb_array[:, 0])
    g_lin = srgb_to_linear(rgb_array[:, 1])
    b_lin = srgb_to_linear(rgb_array[:, 2])
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def extract_frame_from_video(video_path, timestamp_sec=1.0):
    """Extract an uncompressed RGBA PNG frame from a WebM/MP4 video using FFmpeg."""
    tmp_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    cmd = [
        "ffmpeg", "-y",
        "-vcodec", "libvpx-vp9",
        "-i", video_path,
        "-ss", str(timestamp_sec),
        "-vframes", "1",
        "-pix_fmt", "rgba",
        tmp_png
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        # Fallback without explicit vp9 codec specification (e.g. for non-VP9)
        cmd_fallback = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(timestamp_sec),
            "-vframes", "1",
            "-pix_fmt", "rgba",
            tmp_png
        ]
        res_fb = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_fb.returncode != 0:
            raise RuntimeError(f"FFmpeg frame extraction failed: {res.stderr or res_fb.stderr}")
    return tmp_png

def audit_rgba_frame(img_path):
    """Physically analyze an RGBA image for badge geometry, translucency, contrast, and edge variance."""
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {img_path}")
    
    h, w = img.shape[:2]
    has_alpha = (img.shape[2] == 4) if len(img.shape) > 2 else False
    
    if not has_alpha:
        return {
            "status": "FAIL",
            "all_passed": False,
            "error": "Image has no alpha channel (flattened/opaque image rejected, HyperFrames WebM RGBA required)"
        }
    
    b, g, r, a = cv2.split(img)
    rgb = cv2.merge([r, g, b])
    
    # 1. Non-zero alpha mask
    active_mask = a > 20
    active_pixel_count = int(np.sum(active_mask))
    total_screen_pixels = w * h
    screen_area_pct = (active_pixel_count / total_screen_pixels) * 100.0
    
    if active_pixel_count == 0:
        return {
            "status": "FAIL",
            "all_passed": False,
            "reason": "No badge detected on screen (alpha channel completely transparent)"
        }

    # Bounding Box calculations
    y_indices, x_indices = np.where(active_mask)
    x_min, x_max = int(np.min(x_indices)), int(np.max(x_indices))
    y_min, y_max = int(np.min(y_indices)), int(np.max(y_indices))
    bbox_w = x_max - x_min + 1
    bbox_h = y_max - y_min + 1
    
    # 2. Alpha Translucency (Glassmorphism Verification)
    # Background glass plate must be translucent (0.20 <= alpha <= 0.88), NOT opaque (255)
    badge_alpha = a[active_mask]
    translucent_pixels = np.sum((badge_alpha >= 30) & (badge_alpha <= 245))
    translucent_ratio = float(translucent_pixels) / float(active_pixel_count)
    median_alpha = float(np.median(badge_alpha)) / 255.0
    mean_alpha = float(np.mean(badge_alpha)) / 255.0

    # 3. Title Safe Margins
    margin_x_left = (x_min / w) * 100.0
    margin_x_right = ((w - 1 - x_max) / w) * 100.0
    margin_y_top = (y_min / h) * 100.0
    margin_y_bottom = ((h - 1 - y_max) / h) * 100.0
    
    action_safe_5pct = bool((x_min >= 0.05 * w) and (x_max <= 0.95 * w) and (y_min >= 0.05 * h) and (y_max <= 0.95 * h))
    title_safe_8pct = bool((x_min >= 0.08 * w) and (x_max <= 0.92 * w) and (y_min >= 0.08 * h) and (y_max <= 0.92 * h))
    title_safe_10pct = bool((x_min >= 0.10 * w) and (x_max <= 0.90 * w) and (y_min >= 0.10 * h) and (y_max <= 0.90 * h))

    # 4. Contrast Ratio (WCAG 2.1 AA Standard)
    roi_rgb = rgb[active_mask]
    lum = calculate_relative_luminance(roi_rgb)
    
    # Glyphs are in upper percentile (98th), background glass plate is lower median (40th)
    bg_lum = float(np.percentile(lum, 40))
    fg_lum = float(np.percentile(lum, 98))
    
    l1 = max(fg_lum, bg_lum)
    l2 = min(fg_lum, bg_lum)
    contrast_ratio = float((l1 + 0.05) / (l2 + 0.05))

    # 5. Laplacian Sharpness Variance
    roi_gray = cv2.cvtColor(rgb[y_min:y_max+1, x_min:x_max+1], cv2.COLOR_RGB2GRAY)
    laplacian_var = float(cv2.Laplacian(roi_gray, cv2.CV_64F).var())

    # Evaluation Thresholds
    passes_translucency = bool((translucent_ratio >= 0.40) or (0.25 <= median_alpha <= 0.88))
    passes_area = bool((0.5 <= screen_area_pct <= 20.0) and (bbox_w >= 120 and bbox_h >= 50))
    passes_wcag_aa = bool(contrast_ratio >= 4.5)
    passes_sharpness = bool(laplacian_var >= 150.0)
    passes_title_safe = bool(action_safe_5pct)

    all_passed = bool(passes_translucency and passes_area and passes_wcag_aa and passes_sharpness and passes_title_safe)

    return {
        "status": "PASS" if all_passed else "FAIL",
        "all_passed": all_passed,
        "metrics": {
            "resolution": f"{w}x{h}",
            "bbox": {
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_max,
                "y_max": y_max,
                "width": bbox_w,
                "height": bbox_h
            },
            "screen_area_pct": round(screen_area_pct, 2),
            "translucency": {
                "translucent_pixel_ratio": round(translucent_ratio, 3),
                "median_alpha": round(median_alpha, 2),
                "mean_alpha": round(mean_alpha, 2),
                "pass": passes_translucency
            },
            "contrast_wcag_aa": {
                "contrast_ratio": round(contrast_ratio, 2),
                "threshold": 4.5,
                "fg_luminance": round(fg_lum, 4),
                "bg_luminance": round(bg_lum, 4),
                "pass": passes_wcag_aa
            },
            "sharpness": {
                "laplacian_var": round(laplacian_var, 2),
                "threshold": 150.0,
                "pass": passes_sharpness
            },
            "title_safe": {
                "action_safe_5pct": action_safe_5pct,
                "title_safe_8pct": title_safe_8pct,
                "title_safe_10pct": title_safe_10pct,
                "margins_pct": {
                    "left": round(margin_x_left, 1),
                    "right": round(margin_x_right, 1),
                    "top": round(margin_y_top, 1),
                    "bottom": round(margin_y_bottom, 1)
                },
                "pass": passes_title_safe
            }
        }
    }

def scan_codebase_for_pil_draw(directory):
    """Reject static PIL ImageDraw or legacy text-dump code in the generation pipeline."""
    pil_violations = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                        if "ImageDraw.Draw" in content or "from PIL import ImageDraw" in content:
                            # Exclude QA auditor itself
                            if "test_badge_physical_qa" not in f and "hyperframes_overlay_qa" not in f:
                                pil_violations.append(path)
                except Exception:
                    pass
    return pil_violations

def main():
    parser = argparse.ArgumentParser(description="HyperFrames Physical Overlay QA Gate")
    parser.add_argument("input", help="Path to WebM video or RGBA PNG frame")
    parser.add_argument("--timestamp", type=float, default=1.0, help="Timestamp in seconds to sample (default: 1.0s)")
    parser.add_argument("--scan-code", type=str, default=None, help="Directory to scan for forbidden PIL drawing calls")
    args = parser.parse_args()

    # Codebase check
    if args.scan_code and os.path.exists(args.scan_code):
        pil_hits = scan_codebase_for_pil_draw(args.scan_code)
        if pil_hits:
            res = {
                "status": "FAIL",
                "all_passed": False,
                "error": f"PIL drawing detected in generation pipeline! HyperFrames standard violated in: {pil_hits}"
            }
            print(json.dumps(res, indent=2))
            sys.exit(1)

    # Frame extraction or direct image audit
    target_img = args.input
    is_temp = False
    if args.input.lower().endswith((".webm", ".mp4", ".mov", ".mkv")):
        target_img = extract_frame_from_video(args.input, args.timestamp)
        is_temp = True

    try:
        report = audit_rgba_frame(target_img)
        print(json.dumps(report, indent=2))
        sys.exit(0 if report.get("all_passed") else 1)
    finally:
        if is_temp and os.path.exists(target_img):
            try:
                os.remove(target_img)
            except Exception:
                pass

if __name__ == "__main__":
    main()
