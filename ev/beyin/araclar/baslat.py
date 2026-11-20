"""SessionStart hook'u: beyin ozetini baglama basar (~5 KB), tara.py'yi arka planda baslatir. Asla bloklamaz."""
import json, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import KOK, oku, sayfalar, utf8

KANAL_ESLE = [  # cwd parcasi -> kanal sayfasi
    (r"kanallar[\\/]+engineered|documentary_materials|\.gemini[\\/]+scripts", "engineered"),
    (r"kanallar[\\/]+zeropulse|skullstudio", "zeropulse"),
]

def kisalt(s, n=115):
    return s if len(s) <= n else s[: n - 1] + "…"

def main():
    if os.environ.get("BEYIN_ICERDE"):
        return
    try:
        girdi = json.load(sys.stdin)
    except Exception:
        girdi = {}
    cwd = (girdi.get("cwd") or os.getcwd()).lower()
    kaynak = girdi.get("source", "")
    utf8()
    out = [f"# Ortak beyin: {KOK} (tum oturumlar ortak; kurallar README.md)",
           "Uzun/yeni ise baslamadan once: `python C:/Users/meteh/beyin/araclar/ara.py \"konu kelimeleri\"` ile gecmis hatalara bak, sonra <=2 dk mini deneme kos. Gerekirse sayfayi ac (`beyin/<tur>/<ad>.md`). Tum klasoru okuma.",
           "Kalici bir sey ogrenince (cozulen sorun, kullanici kurali, olcum, yeni yol) HEMEN: "
           "`python C:\\Users\\meteh\\beyin\\araclar\\ekle.py --tur ben|ders|konu|kanal|kaynak --ad <ad> --aciklama \"<tek satir>\" --metin \"...\" --kaynak \"...\"`"]
    if kaynak == "compact":
        out.append("**Baglam sikistirildi:** bu oturumda ogrenilen ve beyinde olmayan kalici bilgi varsa simdi ekle.py ile yaz.")
    gruplar = {}
    for tur, p in sayfalar():
        gruplar.setdefault(tur, []).append(p)
    # Oncelik: kanal + acik isler + kullanici once (asla kesilmesin), sonra dersler, en son ad listeleri.
    for desen, kanal in KANAL_ESLE:
        p = KOK / "kanal" / f"{kanal}.md"
        if re.search(desen, cwd) and p.exists():
            out.append(f"\n## Bu klasorun kanali: {kanal}\n" + oku(p)[1].strip()[:900])
            break
    acik = KOK / "acik.md"
    if acik.exists():
        satir = [s for s in acik.read_text(encoding="utf-8").splitlines() if s.startswith("- ")]
        if satir:
            out.append("\n## Acik isler (bitince ekle.py --kapat)\n" + "\n".join(kisalt(s, 160) for s in satir[-12:]))
    if gruplar.get("ben"):
        out.append("\n## Kullanici")
        out += [f"- {p.stem}: {kisalt(oku(p)[0].get('aciklama', ''), 110)}" for p in gruplar["ben"]]
    if gruplar.get("ders"):
        dersler = sorted(gruplar["ders"], key=lambda p: str(oku(p)[0].get("guncel", "")), reverse=True)
        YENI = 8 if kaynak == "compact" else 15  # sikistirma sonrasi taban kucuk kalsin; gerisi ara.py ile bulunur
        out.append("\n## Dersler/kurallar (en yeni once; ayrinti: ara.py ya da beyin/ders/<ad>.md)")
        out += [f"- {p.stem}: {kisalt(oku(p)[0].get("aciklama", ""), 90)}" for p in dersler[:YENI]]
        if dersler[YENI:] and kaynak != "compact":
            out.append("- digerleri: " + ", ".join(p.stem for p in dersler[YENI:]))
    for tur, baslik in (() if kaynak == "compact" else (("konu", "Konu sayfalari"), ("kanal", "Kanallar"), ("kaynak", "Kaynaklar"))):
        if gruplar.get(tur):
            out.append(f"\n## {baslik} (sadece ad; aciklama index.md'de)\n" + ", ".join(p.stem for p in gruplar[tur]))
    # son 2 gunun gunlugunden beyne islenmemis "Aday" satirlari
    aday = []
    for g in sorted((KOK / "gunluk").glob("*.md"))[-2:]:
        for s in g.read_text(encoding="utf-8").splitlines():
            if re.match(r"-\s*Aday:", s):
                aday.append(f"{kisalt(s.strip(), 160)} ({g.stem})")
    if aday:
        out.append("\n## Gunlukten kalici bilgi adaylari (beyinde yoksa ve dogruysa ekle.py ile isle)\n" + "\n".join(aday[-6:]))
    metin = "\n".join(out)
    if len(metin) > 9000:  # sessiz kesme yok
        metin = metin[:9000] + "\n…(ozet kesildi; beyin/index.md'ye bak)"
    print(metin)
    # arka plan taramasi (kendi 30 dk araligini ve kilidini yonetir)
    try:
        bayrak = 0x00000008 | 0x00000200 if os.name == "nt" else 0  # DETACHED_PROCESS | NEW_PROCESS_GROUP
        subprocess.Popen([sys.executable, str(KOK / "araclar" / "tara.py")], cwd=str(KOK / "araclar"),
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=bayrak, close_fds=True)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # hook asla oturumu bozmasin
        print(f"(beyin hook hatasi: {e})")
