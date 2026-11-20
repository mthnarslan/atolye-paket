"""Tekrar tarayici: son N gunun Claude oturum kayitlarinda arac HATA ciktilarini imzaya gore sayar.
Hangi hata hala tekrar ediyor, tuzak.json'da karsiligi var mi, tuzak notu gosterildikten sonra yine olmus mu -> araca gomme adayi.
kullanim: python C:/Users/meteh/Kanallar/tekrar.py [--gun 7]   (haftalik; preflight'a girmez, ~1 dk)
"""
import argparse, collections, glob, json, os, re, time

PROJ = os.path.join(os.path.expanduser("~"), ".claude", "projects")
KURAL = r"C:\Users\meteh\beyin\tuzak.json"
LOG = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "state", "tuzak_log.jsonl")
IMZA = [  # (ad, regex) -- yalniz arac sonucu (tool_result) icinde aranir
    ("charmap", r"UnicodeEncodeError: 'charmap'"),
    ("modul-yok", r"No module named '([\w.]+)"),
    ("json", r"JSONDecodeError|Expecting value: line 1 column 1"),
    ("zaman-asimi", r"ReadTimeout|timed out"),
    ("wsl-bash", r"execvpe|has no installed distributions"),
    ("gitbash-yol", r"C:/Program Files/Git/[a-z]"),
    ("baglanti", r"WinError 10061|Connection refused"),
    ("dosya-kilit", r"WinError 32"),
    ("cuda-oom", r"CUDA out of memory"),
    ("gemweb-model", r"Unknown model name"),
]

ap = argparse.ArgumentParser(); ap.add_argument("--gun", type=float, default=7); a = ap.parse_args()
sinir = time.time() - a.gun * 86400
sayac, oturum, alt = collections.Counter(), collections.defaultdict(set), collections.Counter()
for p in glob.glob(os.path.join(PROJ, "*", "*.jsonl")):
    if os.path.getmtime(p) < sinir:
        continue
    for satir in open(p, encoding="utf-8", errors="replace"):
        if '"tool_result"' not in satir:
            continue
        for ad, rx in IMZA:
            for m in re.finditer(rx, satir):
                sayac[ad] += 1; oturum[ad].add(os.path.basename(p))
                if m.groups():
                    alt[f"{ad}:{m.group(1)}"] += 1
try:
    kurallar = json.load(open(KURAL, encoding="utf-8"))["kurallar"]
except Exception:
    kurallar = []
ates = collections.Counter()
if os.path.exists(LOG):
    for s in open(LOG, encoding="utf-8"):
        try:
            ates[json.loads(s)["kural"].split("@")[0]] += 1
        except Exception:
            pass
print(f"Son {a.gun:g} gun, arac hata ciktilari (imza: sonuc / oturum):")
for ad, n in sayac.most_common():
    print(f"  {ad:13} {n:4} / {len(oturum[ad]):3} oturum")
print("Modul-yok ayrinti:", ", ".join(f"{k.split(':')[1]} {v}" for k, v in alt.most_common(8) if k.startswith("modul")) or "-")
print("Tuzak kurallari (atesleme): " + (", ".join(f"{k['id']} {ates.get(k['id'], 0)}" for k in kurallar) or "-"))
print("Okuma: cok atesleyen + hata surmeye devam eden kural = araca gom, sonra tuzak.json'dan sil. Hic atesmeyen kural = sil.")
