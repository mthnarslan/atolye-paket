"""Yukleme oncesi baslik/aciklama denetimi (tum kanallar). Hakem degil, ALARM: cikan uyariya elle bakilir.
Kullanim:
  python ortak/meta_denetle.py meta.json            # {"title": ..., "description": ...} (yt-dlp info.json da olur)
  python ortak/meta_denetle.py --baslik "..." --aciklama aciklama.txt
Olcum (11-19, testbench/benzerlik_1114 feats, 9 kanalimiz vs 12 insan kanali; ag izleri Holm sonrasi ayiriyor):
  ETIKET: baslikta kurgu etiketi kalintisi (HOOK/SFX/VO/TODO, koseli/kume parantez) -> bizde gercek vaka (Wild Year).
  LINK: aciklamada hic link yok -> bizde 0/31 linkli, insanda 17/22.
  HASHTAG3: aciklama tam 3 hashtag'lik tek satirla bitiyor -> bizde 22/31, insanda 1/22.
Cikis: 0 = uyari yok, 1 = uyari var, 2 = girdi hatasi.
"""
import argparse, json, re, sys
from pathlib import Path

URL = re.compile(r"https?://|www\.", re.I)
HASH = re.compile(r"#\w+")
ETIKET = re.compile(r"\b(HOOK|SFX|VO|B-?ROLL|CTA|TODO|TBD|FIXME|PLACEHOLDER|TITLE|THUMB(NAIL)?|BEAT|MUSIC|MU(Z|S)IK)\b|[\[\]{}<>]|\b[A-Z]{3,}(\s+[A-Z]{2,}){2,}\b")


def denetle(baslik, aciklama):
    U = []
    m = ETIKET.search(baslik or "")
    if m:
        U.append(f"ETIKET: baslikta kurgu etiketi/kalintisi '{m.group(0)}': '{baslik[:90]}'. Yuklemeden once temizle.")
    if not (baslik or "").strip():
        U.append("BASLIK: bos.")
    d = aciklama or ""
    if not URL.search(d):
        U.append("LINK: aciklamada link yok (bizde 0/31, insan 17/22). Kaynak/kanit linklerini (kanit defteri) aciklamaya koy.")
    satir = [x for x in d.split("\n") if x.strip()]
    son = satir[-1] if satir else ""
    hs = HASH.findall(son)
    if len(hs) == 3 and len(HASH.sub("", son).strip()) < 3:
        U.append(f"HASHTAG3: aciklama sabit 3 hashtag satiriyla bitiyor ({' '.join(hs)}; bizde 22/31, insan 1/22). Sayiyi/yeri videoya gore degistir ya da kaldir.")
    return U


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("meta", nargs="?")
    ap.add_argument("--baslik"); ap.add_argument("--aciklama", help="metin dosyasi")
    ap.add_argument("--json")
    a = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        try: s.reconfigure(encoding="utf-8")
        except Exception: pass
    try:
        if a.meta:
            m = json.loads(Path(a.meta).read_text(encoding="utf-8"))
            baslik, aciklama = m.get("title") or m.get("baslik") or "", m.get("description") or m.get("desc") or m.get("aciklama") or ""
        else:
            baslik = a.baslik or ""
            aciklama = Path(a.aciklama).read_text(encoding="utf-8") if a.aciklama else ""
    except Exception as e:
        print(f"girdi hatasi: {e}"); sys.exit(2)
    U = denetle(baslik, aciklama)
    if a.json:
        Path(a.json).write_text(json.dumps({"uyarilar": U}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(U) if U else "uyari yok")
    sys.exit(1 if U else 0)


if __name__ == "__main__":
    main()
