# Ise baslamadan once: konuyla ilgili gecmis ders/hata/cozum satirlarini kisa basar (~1 sn, <=~1.5 KB).
# Kullanim: python ara.py "chatterbox ses" [--n 4]
import re, sys, json
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # 11-16: cp1254 konsolda charmap cokmesi
from ortak import KOK, oku

def norm(s):
    s = s.lower()
    for a, b in zip("çğıöşüâî", "cgiosuai"):
        s = s.replace(a, b)
    return s

def kok(w):
    return w[:5] if len(w) >= 5 else w  # onek koku: Turkce ekler (ajanlari/ajan) icin

def _esanlam():
    try:
        g = json.loads((Path(__file__).parent / "esanlam.json").read_text(encoding="utf-8"))
        return [[norm(t) for t in grup] for grup in g]
    except Exception:
        return []
ESANLAM = _esanlam()
import os
SYNW = float(os.environ.get('ARA_SYN', 0.6)); KOKW = float(os.environ.get('ARA_KOK', 0.4)); ESIK = float(os.environ.get('ARA_ESIK', 0.35))

def kelimeler(s):
    """Her sorgu kelimesi icin (asil kokler, esanlam kokleri) dondurur."""
    sonuc = []
    for w in re.findall(r"[a-z0-9]{2,}", norm(s)):
        if w in {"ile", "icin", "the", "and"}: continue
        asil, esan, tam = {kok(w)}, set(), {w}
        for grup in ESANLAM:
            for t in grup:
                if w == t or (len(t) >= 3 and w.startswith(t)):
                    asil.add(kok(t)); tam.add(t)  # ek almis hal: ajanlari -> ajan
                    esan.update(kok(x) for x in grup if " " not in x)
        if len(w) < 3 and not esan: continue  # tabloda olmayan 2 harfli kelime gurultu
        sonuc.append((tuple(asil), tuple(esan - asil), tuple(tam)))
    return sonuc

def _var(a, metin, sinir=False):
    if len(a) <= 2: return re.search(r"(?<![a-z0-9])" + a + r"(?![a-z0-9])", metin) is not None
    if sinir: return re.search(r"(?<![a-z0-9])" + a, metin) is not None  # esanlam: kelime basi (hang!=change)
    return a in metin

def esles(k, metin):
    """1.0 tam kelime, KOKW yalniz onek koku, SYNW yalniz esanlam, 0 yok."""
    if any(_var(a, metin) for a in k[2]): return 1.0
    if any(_var(a, metin) for a in k[0]): return KOKW
    return SYNW if any(_var(a, metin, True) for a in k[1]) else 0

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 4
    if "--n" in sys.argv: args = [a for a in args if a != str(n)]
    soru = kelimeler(" ".join(args))
    if not soru:
        print("kullanim: ara.py \"konu kelimeleri\""); return
    sonuc = []
    for klasor in ("ders", "konu", "kaynak", "kanal", "ben"):
        for yol in (KOK / klasor).glob("*.md"):
            meta, govde = oku(yol)
            bas = norm(yol.stem + " " + meta.get("aciklama", "") + " " + meta.get("etiket", ""))
            tum = bas + " " + norm(govde)
            kapsam = sum(esles(w, tum) > 0 for w in soru)
            if kapsam * 2 < len(soru): continue  # once ucuz sayfa suzgeci
            agirlik = sum(esles(w, tum) for w in soru)
            satirlar = [s.strip() for s in govde.splitlines() if s.strip() and not s.startswith("#")]
            puan, iyi = 0, []
            for w in soru:
                puan += 3 * esles(w, bas)
            for s in satirlar:
                k = norm(s)
                h = sum(esles(w, k) for w in soru)
                if h: puan += h; iyi.append((h, s))
            if puan:
                puan += 5 * agirlik
                if klasor == "ders": puan += 1
                iyi.sort(key=lambda x: -x[0])
                sonuc.append((puan, f"{klasor}/{yol.stem}", meta.get("aciklama", ""), [s for _, s in iyi[:2]]))
    if not sonuc:
        print("beyinde ilgili kayit yok"); return
    sonuc.sort(key=lambda x: -x[0])
    sonuc = [x for x in sonuc if x[0] >= ESIK * sonuc[0][0]]
    for _, ad, ac, sat in sonuc[:n]:
        print(f"- {ad}: {ac[:160]}")
        for s in sat:
            print(f"    > {s[:220]}")
    if len(sonuc) > n:
        print(f"(+{len(sonuc) - n} sayfa daha; --n ile artir)")

if __name__ == "__main__":
    main()
