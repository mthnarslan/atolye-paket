"""Beyne bilgi ekle / guncelle. Kaydetmek bir komuttur, hatirlanacak kural degil.

  python C:\\Users\\meteh\\beyin\\araclar\\ekle.py --tur ders --ad searxng-cokmesi \\
      --aciklama "SearXNG docker baslamazsa: ..." --metin "Ne oldu, neden, cozum..." \\
      --kaynak "C:\\...\\dosya.py; commit abc123"

Sayfa varsa: aciklama (verildiyse) yenilenir, metin tarihli yeni bolum olarak eklenir.
--metin-dosya ile uzun metin dosyadan okunur. --acik "is" acik.md'ye madde ekler, --kapat "is" siler.
"""
import argparse, sys
from pathlib import Path
from ortak import kilit, KOK, TURLER, ad_temizle, bugun, oku, yaz, index_yap, log, gizli_var, git_kaydet, utf8

utf8()
ap = argparse.ArgumentParser()
ap.add_argument("--tur", choices=list(TURLER))
ap.add_argument("--ad")
ap.add_argument("--aciklama", default="")
ap.add_argument("--metin", default="")
ap.add_argument("--metin-dosya")
ap.add_argument("--kaynak", default="")
ap.add_argument("--etiket", default="")
ap.add_argument("--yazan", default="claude")
ap.add_argument("--acik", help="acik.md'ye acik is ekle")
ap.add_argument("--kapat", help="acik.md'den eslesen isi sil")
a = ap.parse_args()

with kilit():
    if a.acik or a.kapat:
        p = KOK / "acik.md"
        satirlar = p.read_text(encoding="utf-8").splitlines() if p.exists() else ["# Acik isler (her oturum gorur; bitince --kapat)", ""]
        if a.acik:
            satirlar.append(f"- {bugun()} {a.acik}")
            log("acik", a.acik)
        if a.kapat:
            once = len(satirlar)
            satirlar = [s for s in satirlar if not (s.startswith("- ") and a.kapat.lower() in s.lower())]
            log("kapat", f"{a.kapat} ({once - len(satirlar)} madde)")
        p.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
        git_kaydet(f"acik: {a.acik or a.kapat}")
        print("acik.md guncellendi")
        raise SystemExit(0)

    if not (a.tur and a.ad):
        sys.exit("--tur ve --ad gerekli (ya da --acik/--kapat)")
    metin = Path(a.metin_dosya).read_text(encoding="utf-8") if a.metin_dosya else a.metin
    for alan in (metin, a.aciklama, a.kaynak):
        if gizli_var(alan):
            sys.exit("RED: metinde anahtar/parola benzeri bir sey var. Gizli bilgi beyne yazilmaz; dosya yolunu yaz.")
    if not metin.strip() and not a.aciklama:
        sys.exit("--metin ya da --aciklama gerekli")

    ad = ad_temizle(a.ad)
    yol = KOK / a.tur / f"{ad}.md"
    # ayni ad baska turde varsa oraya yaz (cift sayfa olmasin)
    for t in TURLER:
        alt = KOK / t / f"{ad}.md"
        if alt.exists():
            yol = alt
    if yol.exists():
        meta, govde = oku(yol)
        if a.aciklama:
            meta["aciklama"] = a.aciklama
        if a.kaynak:
            meta["kaynak"] = (meta.get("kaynak", "") + "; " + a.kaynak).strip("; ")
        meta["guncel"] = bugun()
        meta["onay"] = ""  # icerik degisti: kullanici onayi yeniden gerekir
        if metin.strip():
            govde = govde.rstrip() + f"\n\n## {bugun()} ({a.yazan})\n\n{metin.strip()}\n"
        islem = "guncelle"
    else:
        if not a.aciklama:
            sys.exit("Yeni sayfa icin --aciklama (tek satir, index'te gorunur) gerekli")
        meta = {"tur": a.tur, "aciklama": a.aciklama, "kaynak": a.kaynak, "olusturma": bugun(),
                "guncel": bugun(), "yazan": a.yazan, "onay": "", "etiket": a.etiket}
        govde = f"# {a.ad}\n\n{metin.strip()}\n"
        islem = "yeni"
    yaz(yol, meta, govde)
    index_yap()
    log(islem, f"{yol.relative_to(KOK).as_posix()} — {meta['aciklama'][:80]}")
    git_kaydet(f"{islem}: {yol.stem}")
    print(f"{islem}: {yol}")
