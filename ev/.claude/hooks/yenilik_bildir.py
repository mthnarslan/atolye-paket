"""UserPromptSubmit hook: SISTEM.md / beyin / Kanallar rehberleri bu oturum son baktigindan beri
degistiyse 2-12 satirlik not basar. Degisiklik yoksa hicbir sey basmaz (token yok, model yok).

Durum: ~/.claude/hooks/state/yenilik_<session_id>.json  {"t": son bakis, "sistem": [satirlar]}
Ilk cagrida (durum yok) yalnizca taban kaydeder, bir sey basmaz: oturum acilisinda SISTEM.md zaten yuklendi.
"""
import json, os, sys, time, glob

HOME = os.path.expanduser("~")
SISTEM = r"C:\Users\meteh\Kanallar\SISTEM.md"
KANALLAR = r"C:\Users\meteh\Kanallar"
BEYIN = r"C:\Users\meteh\beyin"
BEYIN_KLASOR = ("ders", "ben", "kanal")
STATE_DIR = os.path.join(HOME, ".claude", "hooks", "state")
MAX_SATIR = 5      # SISTEM.md'den en fazla bu kadar yeni satir
MAX_DOSYA = 6      # beyin + rehberden en fazla bu kadar dosya
KIRP = 220


def oku_satirlar(p):
    try:
        with open(p, encoding="utf-8") as f:
            return [s.rstrip() for s in f if s.strip()]
    except OSError:
        return []


def aciklama(p):
    try:
        with open(p, encoding="utf-8") as f:
            for i, s in enumerate(f):
                if s.startswith("aciklama:"):
                    return s.split(":", 1)[1].strip()
                if i > 12:
                    break
    except OSError:
        pass
    return ""


def etiket(p):
    try:
        with open(p, encoding="utf-8") as f:
            for i, s in enumerate(f):
                if s.startswith("etiket:"):
                    return s.split(":", 1)[1].strip().lower()
                if i > 12:
                    break
    except OSError:
        pass
    return ""


def kirp(s):
    return s if len(s) <= KIRP else s[:KIRP - 1] + "…"


def main():
    try:
        sid = json.load(sys.stdin).get("session_id") or "x"
    except Exception:
        sid = "x"
    os.makedirs(STATE_DIR, exist_ok=True)
    sp = os.path.join(STATE_DIR, f"yenilik_{sid}.json")
    simdi = time.time()
    sistem = oku_satirlar(SISTEM)
    try:
        with open(sp, encoding="utf-8") as f:
            st = json.load(f)
    except (OSError, ValueError):
        st = None
    if st is None:
        json.dump({"t": simdi, "sistem": sistem}, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
        return
    t0 = st.get("t", simdi)
    notlar = []

    eski = set(st.get("sistem", []))
    yeni = [s for s in sistem if s not in eski]
    if yeni:
        notlar.append(f"SISTEM.md degisti ({len(yeni)} yeni/degisen satir):")
        notlar += ["  " + kirp(s.strip()) for s in yeni[:MAX_SATIR]]
        if len(yeni) > MAX_SATIR:
            notlar.append(f"  … +{len(yeni) - MAX_SATIR}; tamami {SISTEM}")

    dosyalar, yerel = [], 0
    for k in BEYIN_KLASOR:
        for p in glob.glob(os.path.join(BEYIN, k, "*.md")):
            try:
                if os.path.getmtime(p) <= t0:
                    continue
            except OSError:
                continue
            # ben/ (kullanici kurali) ve etiketi 'ortak' iceren kayit herkese gider; gerisi kanala ozel: yalniz sayilir
            if k == "ben" or "ortak" in etiket(p):
                dosyalar.append((os.path.getmtime(p), f"beyin/{k}/{os.path.basename(p)[:-3]}", p))
            else:
                yerel += 1
    for p in glob.glob(os.path.join(KANALLAR, "*.md")):
        b = os.path.basename(p)
        if b in ("SISTEM.md", "SISTEM_arsiv.md", "pano.md"):
            continue
        try:
            if os.path.getmtime(p) > t0:
                dosyalar.append((os.path.getmtime(p), f"Kanallar/{b}", p))
        except OSError:
            pass
    if dosyalar:
        dosyalar.sort(reverse=True)
        notlar.append(f"Yeni/guncel bilgi ({len(dosyalar)} dosya, en yeni once):")
        for _, ad, p in dosyalar[:MAX_DOSYA]:
            a = aciklama(p)
            notlar.append("  " + kirp(f"{ad}: {a}" if a else ad))
        if len(dosyalar) > MAX_DOSYA:
            notlar.append(f"  … +{len(dosyalar) - MAX_DOSYA}; ara.py ile bak")
    if yerel and notlar:
        notlar.append(f"(+{yerel} kanala ozel yeni ders; gerekirse ara.py)")

    json.dump({"t": simdi, "sistem": sistem}, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    if notlar:
        notlar.insert(0, "[yenilik] Bu oturum son baktigindan beri ortak sistemde degisiklik var. Isine dokunuyorsa uygula; dokunmuyorsa gec, kullaniciya anlatma.")
        sys.stdout.reconfigure(encoding="utf-8")
        print("\n".join(notlar))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # hook asla kullanici mesajini engellemez
