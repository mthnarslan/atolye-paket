import sys
import os
import json
import urllib.request
import urllib.error
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vds_secret_store import read_secret

VDS_URL = "http://100.104.78.117:8765/v1/chat/completions"
VDS_API_KEY = read_secret("codex_vds")

ROUTER_URL = "http://100.104.78.117:20128/v1/chat/completions"
ROUTER_API_KEY = read_secret("codex_router")

PROMPT = """Sen dunya capinda uzman bir AI Sistem Mimari, Video Pipeline Muhendisi ve Bas Muhakkiksin.
Kullanicimiz Metehan ile birlikte otonom bir 15 dakikalik (891.2 saniye, 89 sahne, 169 shot/kesit) profesyonel belgesel uretim pipeline'i gelistiriyoruz.

Hedef: Dify uzerinden tek tikla, disaridan sadece proje klasoru verilerek, 15 dakikalik tam belgeseli HICBIR manuel mudahale olmadan, sifirdan EN FAZLA 10 DAKIKA ICINDE (600 saniye) eksiksiz, kurallara %100 sadik ve ultra yuksek kalitede uretmek.

MEVCUT MIMARI VE IS AKISI:
1. Stage 1 (Ses Sentezi): Sopro v2 Turbo CUDA ile 891 saniyelik ses sentezleniyor (master_voiceover.wav, 78 chunk). Sure: ~140s.
2. Stage 2 (Zaman Cizelgesi): Whisper word-level alignment ile metin 89 sahneye ve 169 shot beat'ine bolunuyor. Hedef mix: %50 Video, %25 Foto, %25 3D.
3. Stage 3 (Gorsel Materyaller - documentary_materials):
   - sources.py: YouTube'dan B-roll arar, MP4 indirir, kareler ayiklar.
   - runner.py: 15 eszamanli worker thread calistirir. Her shot icin Flash 3.8 / Codex modeline mikro-istek atarak aday secer veya 3D uret der. Shot MP4'unu render eder. Sonra Codex veya Claude Sonnet modeline ayri bir review istegi atarak kalite kontrol eder. Reddedilirse 3 kez tekrar dener. Aday kalmazsa fallback devreye girer.
4. Stage 4 (NVENC Render): FFmpeg filter_complex ile 169 kesiti tek parca 1080p 25fps NVENC H.264 complete_video.mp4 haline getirir.

YASANAN BUYUK REZALETLER VE SISTEMSEL DARBOGAZLAR:
1. 29 DAKIKA TIMEOUT VE COKUS: 169 shot icin 15 worker deli gibi yuzlerce micro API istegi atti (Flash + Codex + Sonnet). Review modelleri ufacik bahanelerle Attempt 0 ve 1'de reddetti, shot basina 260 saniye bekletti. Dify 29. dakikada fail verdi, 3 shot takili kaldi. Toplam sure 2 saati buldu!
2. KALITE VE ESTETIK FELAKETI (KULLANICININ YAKALADIGI GORUNTU):
   - 07:44'te video calarken ekranda camur gibi bulanik, dusuk cozunurluklu siyah-beyaz bir insaat fotografi cikti!
   - Altinda ise beyaz serit icinde devasa su yazi basildi: "Illustrative local still; extended documentary archive".
   - Profesyonel bir belgeselde boyle cirkin bir aciklama seridi ve bulanik foto kabul edilemez!
3. KURAL IHLALLERI:
   - Kural A (Hook Ilk 30 Saniye): Ilk 30 saniye KESINLIKLE VE SADECE GERCEK HAREKETLI VIDEO KESITI olmak zorunda. Asla 3D, fotograf veya kart olamaz. Bu kural ihlal edildi.
   - Kural B (Maksimum 2 Kesit): Bir YouTube kaynak videosundan en fazla 2 kesit alinabilir. Bu asildi.
   - Kural C (Sifir Yinelenen Materyal): Bir gorsel/materyal (ozellikle 3D model veya fotograf) asla 2. kez kullanilamaz. Fallback mekanizmasi havuz tukenince all_photos[(shot_id-1)%len] diyerek ayni fotografi defalarca tekrar tekrar kullandi!

SENDEN SISTEMSEL VE MIMARI OLARAK SUNLARI CEVAPLAMANI ISTIYORUZ:
1. Neden 169 ayri micro LLM secim istegi ve 169 ayri review istegi atiyoruz? Bunun yerine 1-3 adet MAKRO-PLANLAMA (Global Batch Allocation) LLM istegi ile tum 169 kesitin video/foto/3D dagilimi, zaman araliklari ve kaynak eslesmesi tek seferde yapilamaz mi?
2. Kurallari (Ilk 30s video zorunlulugu, kaynak basina max 2 kesit, sifir materyal tekrari, min 1080p cozunurluk) LLM'in insafina veya review filtrelerine birakmak yerine KOD SEVIYESINDE DETERMINISTIK OLARAK nasil garanti altina aliriz?
3. Cirkin "Illustrative local still" disclaimeri ve bulanik dusuk cozunurluklu gorseller sistemden nasil tamamen kazinir? Yetersiz materyal durumunda dinamik procedural 3D veya akilli kamera hareketleri nasil devreye girmeli?
4. Tum 15 dakikalik videonun sifirdan (temiz klasorden) nihai NVENC MP4'e kadar 10 DAKIKA (600 saniye) altinda takir takir cikmasi icin ideal mimari blueprint'i adim adim kod ornekleri ve mimari sema ile ciz.

Detayli, teknik, cerrahi ve acimasizca durust bir analiz yap. Yuzeyde kalma, gercek muhendislik cikarimlari ver!
"""

def stream_query(url, key, model, prompt, timeout=180):
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    parts = []
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data: ") and not l.startswith("data: [DONE]"):
                try:
                    chunk = json.loads(l[6:])
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        parts.append(delta["content"])
                except Exception:
                    pass
    res = "".join(parts).strip()
    dur = round(time.time() - t0, 1)
    return res, dur

if __name__ == "__main__":
    out_dir = Path(r"C:\Users\meteh\.gemini\antigravity\brain\519fe672-73a8-4624-999d-0643c27eb7f4\consultation")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target in ("all", "gpt"):
        try:
            print("[GPT] Querying gpt-6.1-sol via VDS (port 8765) with streaming...", flush=True)
            res, dur = stream_query(VDS_URL, VDS_API_KEY, "gpt-6.1-sol", PROMPT, timeout=180)
            with open(out_dir / "response_gpt_6_1_sol.md", "w", encoding="utf-8") as f:
                f.write(res)
            print(f"[GPT] Completed in {dur}s ({len(res)} chars). Saved to response_gpt_6_1_sol.md", flush=True)
        except Exception as e:
            print(f"[GPT] FAILED: {e}", flush=True)

    if target in ("all", "claude"):
        try:
            print("[Claude] Querying ag/claude-opus-4-6-thinking via 9Router (port 20128) with streaming...", flush=True)
            res, dur = stream_query(ROUTER_URL, ROUTER_API_KEY, "ag/claude-opus-4-6-thinking", PROMPT, timeout=180)
            with open(out_dir / "response_claude_opus_4_6.md", "w", encoding="utf-8") as f:
                f.write(res)
            print(f"[Claude] Completed in {dur}s ({len(res)} chars). Saved to response_claude_opus_4_6.md", flush=True)
        except Exception as e:
            print(f"[Claude] FAILED: {e}", flush=True)
