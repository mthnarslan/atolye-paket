"""Kanal durum panosu: her kanal oturumu Kanallar/pano.md'de KENDI tek satirini gunceller (eklemez, ustune yazar).
kullanim: python C:/Users/meteh/Kanallar/pano.py --kanal Survival --durum "ep03 render 12/40; Drive'a yukleme hazir"
          python C:/Users/meteh/Kanallar/pano.py            (panoyu goster)
Satir <=160 karakter. Yalniz 'su an ne yapiyor / ne bekliyor'. Kalici bilgi buraya degil beyne (ekle.py) gider.
"""
import argparse, os, re, time

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pano.md")
BASLIK = "# Kanal panosu (her kanal tek satir; pano.py ile guncellenir, elle yazma)\n"
MAX = 160

ap = argparse.ArgumentParser()
ap.add_argument("--kanal")
ap.add_argument("--durum")
a = ap.parse_args()

satirlar = []
if os.path.exists(P):
    satirlar = [s.rstrip("\n") for s in open(P, encoding="utf-8") if s.startswith("- **")]

if a.kanal and a.durum is not None:
    d = " ".join(a.durum.split())
    if len(d) > MAX:
        d = d[:MAX - 1] + "…"
    yeni = f"- **{a.kanal}** ({time.strftime('%m-%d %H:%M')}): {d}"
    kalip = re.compile(r"^- \*\*" + re.escape(a.kanal) + r"\*\* ")
    satirlar = [s for s in satirlar if not kalip.match(s)] + [yeni]
    satirlar.sort(key=lambda s: s.split("**")[1].lower())
    with open(P, "w", encoding="utf-8") as f:
        f.write(BASLIK + "\n".join(satirlar) + "\n")
    print(yeni)
else:
    print(BASLIK + "\n".join(satirlar))
