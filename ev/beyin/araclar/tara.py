"""Arka plan taramasi (SessionStart hook'u ayrik baslatir; elle de calisir).
1) Projelerin auto-memory dosyalarini beyne aktarir (kaynak yolu + mtime ile; degismeyen tekrar yazilmaz).
2) Son taramadan beri buyuyen oturum kayitlarinin yeni kismini Haiku ile gunluk/YYYY-MM-DD.md'ye ozetler.
Otomatik ozet kalici sayfaya YAZMAZ; "Aday" satirlari sonraki oturumlara gosterilir, kalicilastirma ekle.py ile.

  python tara.py            # normal (30 dk'dan sik calismaz)
  python tara.py --simdi    # araliga bakmadan
  python tara.py --sadece-hafiza
"""
import datetime, json, os, re, shutil, subprocess, sys, time
from pathlib import Path
from ortak import KOK, kilit, oku, yaz, ad_temizle, bugun, index_yap, log, gizli_var, git_kaydet, atomik, utf8

utf8()
PROJ = Path.home() / ".claude" / "projects"
DURUM = KOK / ".tara_durum.json"
ARALIK = 30 * 60
ESIK = 1500          # bundan az yeni metin ozetlenmez
KESIT = 24000        # Haiku'ya giden en fazla karakter
TUR = {"user": "ben", "feedback": "ders", "project": "konu", "reference": "kaynak"}

def durum_oku():
    try:
        return json.loads(DURUM.read_text(encoding="utf-8"))
    except Exception:
        return {"son": 0, "kayit": {}, "hafiza": {}}

def proje_adi(klasor):
    ad = klasor.name.replace("C--Users-meteh-", "").replace("C--Users-meteh", "ev")
    return ad.strip("-")[:40] or "ev"

def atla(klasor):
    n = klasor.name.lower()
    return "beyin" in n or "scratch" in n or "appdata" in n or "temp" in n

# ---------- 1) auto-memory aktarimi ----------
try:
    ALIAS = json.loads((KOK / "araclar" / "birlesik.json").read_text(encoding="utf-8"))  # eski ad -> birlestirilen sayfa
except Exception:
    ALIAS = {}

def tirnaksiz(s):
    s = s.replace("\n", " ").strip()
    if len(s) > 1 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].replace('\\"', '"')
    return s
def hafiza_aktar(d):
    yeni = 0
    for md in PROJ.glob("*/memory/*.md"):
        if md.name == "MEMORY.md" or atla(md.parent.parent):
            continue
        anahtar, mt = str(md), md.stat().st_mtime
        if d["hafiza"].get(anahtar) == mt:
            continue
        m, govde = oku(md)
        if gizli_var(govde):
            d["hafiza"][anahtar] = mt
            log("atla-gizli", anahtar)
            continue
        tur = TUR.get(m.get("type", ""), "konu")
        ad = ad_temizle(m.get("name") or md.stem)
        ad = ALIAS.get(ad, ad)
        if not ad:  # birlesik.json'da "" = bilerek silindi, yeniden aktarma
            d["hafiza"][anahtar] = mt
            continue
        hedef = next((KOK / t / f"{ad}.md" for t in TUR.values() if (KOK / t / f"{ad}.md").exists()), KOK / tur / f"{ad}.md")
        kaynak = f"auto-memory {md.parent.parent.name}/memory/{md.name}"
        if hedef.exists():
            hm, hg = oku(hedef)
            if govde.strip() in hg:
                d["hafiza"][anahtar] = mt
                continue
            hg = hg.rstrip() + f"\n\n## {bugun()} (auto-memory guncellemesi: {md.parent.parent.name})\n\n{govde.strip()}\n"
            hm["guncel"] = bugun(); hm["onay"] = ""
            if kaynak not in hm.get("kaynak", ""):
                hm["kaynak"] = (hm.get("kaynak", "") + "; " + kaynak).strip("; ")
            yaz(hedef, hm, hg)
            log("hafiza-guncelle", hedef.relative_to(KOK).as_posix())
        else:
            g = datetime.date.fromtimestamp(mt).isoformat()
            yaz(hedef, {"tur": tur, "aciklama": (m.get("description") or ad).replace("\n", " "), "kaynak": kaynak,
                        "olusturma": g, "guncel": g, "yazan": "auto-memory", "onay": "", "etiket": ""}, govde)
            log("hafiza-yeni", hedef.relative_to(KOK).as_posix())
        d["hafiza"][anahtar] = mt
        yeni += 1
    return yeni

# ---------- 2) oturum gunlugu ----------
SR = re.compile(r"<system-reminder>.*?</system-reminder>|<command-[a-z\-]+>.*?</command-[a-z\-]+>", re.S)

def metin_cikar(yol, bas):
    parca, cwd = [], ""
    with open(yol, "rb") as f:
        f.seek(bas)
        veri = f.read()
    for satir in veri.decode("utf-8", "replace").splitlines():
        try:
            o = json.loads(satir)
        except Exception:
            continue
        cwd = o.get("cwd") or cwd
        tip = o.get("type")
        if tip not in ("user", "assistant") or o.get("isMeta") or o.get("isSidechain"):
            continue
        c = (o.get("message") or {}).get("content")
        if isinstance(c, str):
            t = c
        elif isinstance(c, list):
            t = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
        else:
            continue
        t = SR.sub("", t).strip()
        if not t or t.startswith("This session is being continued") or "<task-notification>" in t:
            continue
        parca.append(("KULLANICI: " if tip == "user" else "CLAUDE: ") + t[:3000])
    return "\n\n".join(parca), cwd

ISTEM = """Asagida bir Claude Code oturumunun bir kesiti var (kullanici Turkce konusur). Ortak "beyin" gunlugu icin ozetle.
Kurallar: Turkce, en fazla 8 madde, her madde tek satir, somut (dosya yolu, sayi, karar). Uydurma; kesitte yoksa yazma.
Bicim (bos kalan satiri hic yazma):
- Is: <ne uzerinde calisildi, tek satir>
- Yapildi: ...
- Karar: <kullanicinin verdigi karar/tercih>
- Acik: <yarim kalan is>
- Aday: <baska oturumlarin da bilmesi gereken kalici bilgi: cozulmus sorun, kural, olcum, yeni arac/yol>
Kesitte kayda deger bir sey yoksa sadece YOK yaz.

KESIT:
"""

def haiku(metin):
    env = dict(os.environ, BEYIN_ICERDE="1")
    (KOK / ".tara").mkdir(exist_ok=True)
    exe = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe")
    r = subprocess.run([exe, "-p", "--model", "haiku", "--no-session-persistence", "--setting-sources", "project"],
                       input=ISTEM + metin, capture_output=True, text=True, encoding="utf-8", timeout=240,
                       cwd=KOK / ".tara", env=env,
                       creationflags=0x08000000 if os.name == "nt" else 0)  # CREATE_NO_WINDOW
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[:300])
    return r.stdout.strip()

def gunluk_yaz(d, tek=None, gecmis_saat=12):
    simdi = time.time()
    yazildi = 0
    for j in PROJ.glob("*/*.jsonl"):
        if atla(j.parent):
            continue
        anahtar, boy = str(j), j.stat().st_size
        onceki = d["kayit"].get(anahtar)
        if onceki is None:
            # ilk gorus: 12 saatten eskiyse sadece isaretle
            if simdi - j.stat().st_mtime > gecmis_saat * 3600:
                d["kayit"][anahtar] = boy
                continue
            onceki = 0
        if boy <= onceki:
            continue
        metin, cwd = metin_cikar(j, onceki)
        if len(metin) < ESIK:
            continue  # birikmesini bekle; ofset ilerlemez
        try:
            ozet = haiku(metin[-KESIT:])
        except Exception as e:
            log("tara-hata", f"{j.name}: {e}")
            if "authenticate" in str(e):
                break  # CLI oturumu dusmus: kalan dosyalar icin bos claude -p acma (11-19)
            continue
        d["kayit"][anahtar] = boy
        if not ozet or ozet.strip().upper().startswith("YOK") or gizli_var(ozet):
            continue
        gun = datetime.date.today().isoformat()
        p = KOK / "gunluk" / f"{gun}.md"
        bas = p.read_text(encoding="utf-8") if p.exists() else f"---\ntur: gunluk\naciklama: {gun} oturum ozetleri (otomatik, Haiku)\n---\n# {gun}\n"
        baslik = f"\n### {datetime.datetime.now():%H:%M} · {proje_adi(j.parent)} · {j.stem[:8]}\n"
        if cwd:
            baslik += f"`{cwd}`\n"
        atomik(p, bas.rstrip() + "\n" + baslik + ozet.strip() + "\n")
        yazildi += 1
        if tek and yazildi >= tek:
            break
    return yazildi

def main():
    if os.environ.get("BEYIN_ICERDE"):
        return
    arg = sys.argv[1:]
    d = durum_oku()
    if "--simdi" not in arg and time.time() - d.get("son", 0) < ARALIK:
        return
    try:
        with kilit("tara", bekle=0):
            with kilit():
                h = hafiza_aktar(d)
                if h:
                    index_yap()
            d["son"] = time.time()
            atomik(DURUM, json.dumps(d))
            gs = int(arg[arg.index("--gecmis-saat") + 1]) if "--gecmis-saat" in arg else 12
            g = 0 if "--sadece-hafiza" in arg else gunluk_yaz(d, tek=int(arg[arg.index("--tek") + 1]) if "--tek" in arg else None, gecmis_saat=gs)
            atomik(DURUM, json.dumps(d))
            if h or g:
                with kilit():
                    git_kaydet(f"tara: {h} hafiza, {g} gunluk")
            print(f"tara: {h} hafiza notu, {g} gunluk ozeti")
    except TimeoutError:
        print("tara: baska kopya calisiyor")

if __name__ == "__main__":
    main()
