# Beyin ortak yardimcilar: sayfa okuma/yazma, index uretimi, log, gizli bilgi kontrolu.
import contextlib, datetime, os, re, subprocess, sys, time
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
TURLER = {"ben": "ben", "ders": "ders", "konu": "konu", "kanal": "kanal", "kaynak": "kaynak"}
BASLIK = {"ben": "Ben (kullanici, tercihler)", "ders": "Dersler / kurallar (cozulmus sorunlar)",
          "konu": "Konular (sistem bilgisi)", "kanal": "Kanallar", "kaynak": "Kaynaklar (veri, link, arac)"}
GIZLI = re.compile(r"(AIza[0-9A-Za-z_\-]{30,}|sk-[A-Za-z0-9_\-]{20,}|ghp_[A-Za-z0-9]{30,}|xox[bp]-[A-Za-z0-9\-]{20,}"
                   r"|-----BEGIN [A-Z ]*PRIVATE KEY|(?i:password|parola|sifre)\s*[:=]\s*\S{6,})")

def bugun():
    return datetime.date.today().isoformat()

def ad_temizle(ad):
    ad = ad.strip().lower()
    for a, b in zip("çğıöşüâî ", "cgiosuai-"):
        ad = ad.replace(a, b)
    return re.sub(r"[^a-z0-9\-]", "", ad).strip("-")[:60] or "adsiz"

def oku(yol):
    """(meta dict, govde str). Basit 'anahtar: deger' front matter."""
    t = Path(yol).read_text(encoding="utf-8", errors="replace")
    meta, govde = {}, t
    if t.startswith("---"):
        son = t.find("\n---", 3)
        if son > 0:
            for satir in t[3:son].strip().splitlines():
                if ":" in satir:
                    k, v = satir.split(":", 1)
                    meta[k.strip()] = v.strip()
            govde = t[son + 4:].lstrip("\n")
    return meta, govde

def yaz(yol, meta, govde):
    sira = ["tur", "aciklama", "kaynak", "olusturma", "guncel", "yazan", "onay", "etiket"]
    satirlar = [f"{k}: {meta[k]}" for k in sira if k in meta]
    satirlar += [f"{k}: {v}" for k, v in meta.items() if k not in sira]
    atomik(yol, "---\n" + "\n".join(satirlar) + "\n---\n" + govde.rstrip() + "\n")

def atomik(yol, metin):
    gecici = Path(str(yol) + ".tmp")
    gecici.write_text(metin, encoding="utf-8")
    os.replace(gecici, yol)

@contextlib.contextmanager
def kilit(ad="yazma", bekle=60):
    """Ayni anda tek yazici (birden cok oturum). 10 dk'dan eski kilit bayat sayilir."""
    k = KOK / f".kilit-{ad}"
    bas = time.time()
    while True:
        try:
            fd = os.open(k, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - k.stat().st_mtime > 600:
                    k.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.time() - bas > bekle:
                raise TimeoutError(f"kilit alinamadi: {k}")
            time.sleep(0.3)
    try:
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            k.unlink()

def sayfalar():
    for tur in TURLER:
        for p in sorted((KOK / tur).glob("*.md")):
            yield tur, p

def index_yap():
    out = ["# Beyin indeksi", "",
           "Her satir: [[sayfa]] — tek satir aciklama. Once burayi oku, sadece gereken sayfayi ac.",
           f"Guncelleme: {bugun()} · araclar/ekle.py otomatik yazar, elle duzenleme.", ""]
    for tur in TURLER:
        satir = []
        for _, p in [x for x in sayfalar() if x[0] == tur]:
            m, _g = oku(p)
            onay = " ✓" if m.get("onay") else ""
            satir.append(f"- [[{p.stem}]] — {m.get('aciklama', '(aciklama yok)')}{onay}")
        if satir:
            out += [f"## {BASLIK[tur]}", ""] + satir + [""]
    atomik(KOK / "index.md", "\n".join(out) + "\n")

def log(islem, ne):
    with open(KOK / "log.md", "a", encoding="utf-8") as f:
        f.write(f"- {datetime.datetime.now():%Y-%m-%d %H:%M} {islem}: {ne}\n")

def gizli_var(metin):
    return GIZLI.search(metin or "")

def git_kaydet(mesaj):
    try:
        subprocess.run(["git", "-C", str(KOK), "add", "-A"], capture_output=True, timeout=30)
        subprocess.run(["git", "-C", str(KOK), "commit", "-q", "-m", mesaj], capture_output=True, timeout=30)
    except Exception:
        pass

def utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
