"""Ortak teslim araci: SFX kapisi + tek Drive yukleme isci kuyrugu. ZIP yok, mp4 dogrudan.

  python teslim.py ekle film.mp4 --sfx sfx.json --hedef <drive klasoru> [--kok-id ID] [--golge] [--qa-cikti DIR]
      sfx_qa.py kosar. Normal mod: cikis 1/2 = kuyruga ALMAZ, o kodu doner (0 = kuyruga alindi).
      --golge: sonuc ne olursa olsun kuyruga alir, rapor/durumda "golge_qa_kodu" ile isaretler, cikis 0.
      Ayni dosya (yol+boyut+mtime) ikinci kez girmez (cikis 0, "zaten kuyrukta/yuklendi").
  python teslim.py isci [--bekle SN] [--parca 64M] [--es 1]
      Tek yukleme isci (msvcrt kilidi; ikinci ornek hemen cikar, kod 4). Kuyrugu sirayla yukler,
      uzak boyut esitse "tamam" yazar, yerel dosyayi SILMEZ. Sonuc: <kuyruk>/durum.json.
  python teslim.py durum

Hedef: rclone 'gdrive:' altindaki klasor yolu; --kok-id verilirse --drive-root-folder-id olarak eklenir.
Kuyruk dizini: TESLIM_KUYRUK ortam degiskeni, yoksa Kanallar/ortak/_teslim_kuyruk.
NOT: sfx_qa.py GPU KULLANMIYOR (numpy/scipy CPU, ffmpeg CPU, Gemini uzaktan); ileride GPU kullanirsa
burada ekle() icinde gpu_tts.lock alinmali (TODO, bkz KONSEY_KARAR madde 2).
Cikis: 0 tamam; 1/2 sfx_qa kodu; 3 hatali girdi; 4 isci zaten calisiyor; 5 yukleme hatasi var.
"""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

Q = Path(os.environ.get("TESLIM_KUYRUK", r"C:\Users\meteh\Kanallar\ortak\_teslim_kuyruk"))
RC = r"C:\Users\meteh\tools_dl\rclone_dl\rclone-v1.76.0-windows-amd64\rclone.exe"
SFXQA = r"C:\Users\meteh\Kanallar\sfx_qa.py"
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")


def yaz(p, d):
    t = Path(str(p) + ".tmp%d" % os.getpid())
    t.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf8")
    os.replace(t, p)


def oku(p):
    return json.loads(Path(p).read_text(encoding="utf8"))


def dosya_id(f):
    st = os.stat(f)
    return hashlib.sha1(("%s|%d|%d" % (os.path.abspath(f).lower(), st.st_size, st.st_mtime_ns)).encode()).hexdigest()[:16]


def ekle(a):
    f = os.path.abspath(a.film)
    if not os.path.isfile(f) or not os.path.isfile(a.sfx):
        print("film/sfx yok"); return 3
    (Q / "items").mkdir(parents=True, exist_ok=True)
    i = dosya_id(f); ip = Q / "items" / (i + ".json")
    if ip.exists():
        print("MUKERRER: zaten kuyrukta/yuklendi (%s, durum=%s)" % (i, oku(ip).get("durum"))); return 0
    t0 = time.time(); od = a.qa_cikti or str(Q / "qa" / i)
    q = subprocess.run([sys.executable, SFXQA, f, os.path.abspath(a.sfx), od], env=ENV)
    kod = q.returncode
    if kod and not a.golge:
        print("TESLIM DUR: sfx_qa kodu %d, kuyruga alinmadi (rapor %s/sfx_qa.json)" % (kod, od)); return kod
    if ip.exists(): return 0  # QA sirasinda baska ekleme girdiyse
    yaz(ip, {"id": i, "dosya": f, "boyut": os.path.getsize(f), "hedef": a.hedef, "kok_id": a.kok_id,
             "golge": bool(a.golge), "qa_kodu": kod, "golge_qa_kodu": kod if (a.golge and kod) else None,
             "qa_rapor": od + "/sfx_qa.json", "qa_sn": round(time.time() - t0, 1),
             "eklendi": time.time(), "durum": "bekliyor", "deneme": 0})
    print("KUYRUGA ALINDI %s%s" % (i, " [GOLGE: sfx_qa kodu %d, normal modda engellenirdi]" % kod if (a.golge and kod) else ""))
    return 0


class Kilit:
    def __enter__(self):
        import msvcrt
        Q.mkdir(parents=True, exist_ok=True)
        self.f = open(Q / "isci.lock", "a+b")
        try:
            self.f.seek(0); msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1); return True
        except OSError:
            self.f.close(); return False

    def __exit__(self, *e):
        import msvcrt
        try:
            self.f.seek(0); msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception: pass
        self.f.close()


def uzak_boyut(it):
    d = it["hedef"].replace("\\", "/").rstrip("/")
    a = [RC, "lsjson", "gdrive:" + d, "--files-only", "-q"] + (["--drive-root-folder-id", it["kok_id"]] if it.get("kok_id") else [])
    r = subprocess.run(a, capture_output=True, text=True, env=ENV)
    if r.returncode: return None
    for x in json.loads(r.stdout or "[]"):
        if x["Name"] == os.path.basename(it["dosya"]): return x["Size"]
    return None


def yukle(it, parca, es):
    d = it["hedef"].replace("\\", "/").rstrip("/")
    a = [RC, "copy", it["dosya"], "gdrive:" + d, "-q", "--drive-chunk-size", parca, "--transfers", str(es)]
    if it.get("kok_id"): a += ["--drive-root-folder-id", it["kok_id"]]
    return subprocess.run(a, capture_output=True, text=True, env=ENV)


def isci(a):
    with Kilit() as ok:
        if not ok:
            print("isci zaten calisiyor"); return 4
        dp = Q / "durum.json"; hata = 0; isci.son = time.time()
        while True:
            bek = sorted((oku(p) for p in (Q / "items").glob("*.json")), key=lambda x: x["eklendi"])
            bek = [x for x in bek if x["durum"] == "bekliyor" or (x["durum"] == "hata" and x["deneme"] < 3)]
            if not bek:
                if a.bekle and time.time() - getattr(isci, "son", time.time()) < a.bekle:
                    time.sleep(5); continue
                break
            it = bek[0]; ip = Q / "items" / (it["id"] + ".json")
            if not os.path.isfile(it["dosya"]):
                it.update(durum="hata", hata="yerel dosya yok", deneme=9); yaz(ip, it); hata += 1; continue
            it.update(durum="yukleniyor", deneme=it["deneme"] + 1, yukleme_bas=time.time()); yaz(ip, it)
            r = yukle(it, a.parca, a.es); ub = uzak_boyut(it); bit = time.time()
            if ub == it["boyut"]:  # olcut uzak boyut; rclone cikis kodu yalniz not (11-18: bir kosuda dosya yuklendi, go runtime crash kodu 2)
                sn = bit - it["yukleme_bas"]
                it.update(durum="tamam", dogrulandi=bit, uzak_boyut=ub, yukleme_sn=round(sn, 1),
                          mb_s=round(it["boyut"] / 1048576 / max(sn, .01), 2), ekle_dogrulama_sn=round(bit - it["eklendi"], 1),
                          parca=a.parca, es=a.es, rclone_kod=r.returncode, hata=None)
            else:
                it.update(durum="hata", hata="rclone kod %s, uzak boyut %s != %s: %s" % (r.returncode, ub, it["boyut"], (r.stderr or "")[:300])); hata += 1
            yaz(ip, it); isci.son = time.time()
            tum = [oku(p) for p in (Q / "items").glob("*.json")]
            yaz(dp, {"guncelleme": time.time(), "tamam": sum(x["durum"] == "tamam" for x in tum),
                     "bekliyor": sum(x["durum"] == "bekliyor" for x in tum), "hata": sum(x["durum"] == "hata" for x in tum),
                     "son": {k: it.get(k) for k in ("id", "dosya", "durum", "uzak_boyut", "yukleme_sn", "mb_s", "ekle_dogrulama_sn", "golge_qa_kodu", "hata")}})
            print(it["id"], it["durum"], it.get("mb_s"), "MB/s", it.get("hata") or "")
        return 5 if hata else 0


def durum(a):
    for p in sorted((Q / "items").glob("*.json")):
        x = oku(p); print(x["id"], x["durum"], os.path.basename(x["dosya"]), x.get("mb_s"), x.get("golge_qa_kodu"))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); s = ap.add_subparsers(dest="c", required=True)
    e = s.add_parser("ekle"); e.add_argument("film"); e.add_argument("--sfx", required=True); e.add_argument("--hedef", required=True)
    e.add_argument("--kok-id"); e.add_argument("--golge", action="store_true"); e.add_argument("--qa-cikti")
    w = s.add_parser("isci"); w.add_argument("--bekle", type=int, default=0); w.add_argument("--parca", default="64M"); w.add_argument("--es", type=int, default=1)
    s.add_parser("durum")
    a = ap.parse_args(); sys.exit({"ekle": ekle, "isci": isci, "durum": durum}[a.c](a))
