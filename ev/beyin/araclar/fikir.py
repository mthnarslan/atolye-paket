"""Karar anlarinda ikinci goz: ayni soruyu gemweb hydrogen (high) modeline sorar. Sadece fikir; karari cagiran oturum verir.
11-19: GPT (VDS/codex astra) ve 9router Flash bitti; tek yol gemweb :8790. Asil karsi-tez icin Sonnet alt ajani (SISTEM.md).

  python C:/Users/meteh/beyin/araclar/fikir.py "soru" [--dosya baglam.md]
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\meteh\Kanallar")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8")
    except Exception: pass
import gemweb

ap = argparse.ArgumentParser()
ap.add_argument("soru")
ap.add_argument("--dosya", action="append", default=[])
ap.add_argument("--sadece", help="eski secenek; yok sayilir")
a = ap.parse_args()
baglam = "\n\n".join(f"### {p}\n{Path(p).read_text(encoding='utf-8')[:20000]}" for p in a.dosya)
istem = ("Bir tasarim kararinda ikinci goz olarak fikir veriyorsun. Kisa ve somut ol: en fazla 8 madde, "
         "her biri tek cumle; katilmadigin yeri ve en guclu karsi argumani acikca soyle; Turkce yaz.\n\n"
         + a.soru + ("\n\nBAGLAM:\n" + baglam if baglam else ""))
try:
    print("===== GEMWEB =====\n" + gemweb.sor(istem, effort="high"))
except Exception as e:
    print(f"===== GEMWEB =====\n(HATA: {e})")
