"""Beyin saglik raporu (deterministik; sadece rapor verir, duzeltmez).
  python lint.py            # ekrana
  python lint.py --yaz      # ayrica lint_raporu.md
"""
import datetime, difflib, re, sys
from ortak import KOK, oku, sayfalar, gizli_var, utf8

utf8()
LINK = re.compile(r"\[\[([^\]|#]+)")
ESKI_GUN = 60
s = {p.stem: (tur, p) for tur, p in sayfalar()}
ekler = {"index", "acik", "log", "README"}
sorun = {k: [] for k in ["aciklama", "kaynak", "kirik", "yetim", "eski", "cift", "gizli", "uzun"]}
gelen = {k: 0 for k in s}
bugun = datetime.date.today()
meta = {}
for ad, (tur, p) in s.items():
    m, g = oku(p)
    meta[ad] = m
    if not m.get("aciklama"):
        sorun["aciklama"].append(ad)
    elif len(m["aciklama"]) > 200:
        sorun["uzun"].append(f"{ad} ({len(m['aciklama'])} karakter)")
    if not m.get("kaynak"):
        sorun["kaynak"].append(ad)
    for hedef in LINK.findall(g):
        h = hedef.strip()
        if h in gelen:
            if h != ad:
                gelen[h] += 1
        elif h not in ekler:
            sorun["kirik"].append(f"{ad} → [[{h}]]")
    try:
        gun = (bugun - datetime.date.fromisoformat(m.get("guncel", "")[:10])).days
        if gun > ESKI_GUN:
            sorun["eski"].append(f"{ad} ({gun} gun)")
    except ValueError:
        pass
    if gizli_var(g):
        sorun["gizli"].append(ad)
for f in ("acik.md",):
    p = KOK / f
    if p.exists():
        for h in LINK.findall(p.read_text(encoding="utf-8")):
            if h.strip() in gelen:
                gelen[h.strip()] += 1
sorun["yetim"] = [a for a, n in gelen.items() if n == 0 and s[a][0] in ("konu", "kaynak")]
adlar = list(s)
for i, a in enumerate(adlar):
    for b in adlar[i + 1:]:
        ra = difflib.SequenceMatcher(None, a, b).ratio()
        rd = difflib.SequenceMatcher(None, meta[a].get("aciklama", ""), meta[b].get("aciklama", "")).ratio()
        if (ra > 0.75 and rd > 0.4) or rd > 0.7:
            sorun["cift"].append(f"{a} ~ {b} (ad {ra:.2f}, aciklama {rd:.2f})")
aday = 0
for g in sorted((KOK / "gunluk").glob("*.md"))[-7:]:
    aday += len(re.findall(r"^-\s*Aday:", g.read_text(encoding="utf-8"), re.M))

BASLIK = {"gizli": "GIZLI BILGI (hemen temizle)", "kirik": "Kirik link", "cift": "Olasi cift sayfa (birlestir, birlesik.json'a yaz)",
          "aciklama": "Aciklamasi yok", "kaynak": "Kaynagi yok", "uzun": "Aciklama cok uzun (>200)",
          "eski": f"{ESKI_GUN} gunden eski (dogrula ya da guncelle)", "yetim": "Yetim konu/kaynak (hic link almiyor)"}
out = [f"# Beyin lint raporu {bugun}", f"{len(s)} sayfa · son 7 gun gunlukte {aday} 'Aday' satiri", ""]
for k in ["gizli", "kirik", "cift", "aciklama", "kaynak", "uzun", "eski", "yetim"]:
    if sorun[k]:
        out.append(f"## {BASLIK[k]}: {len(sorun[k])}")
        out += [f"- {x}" for x in sorun[k][:40]] + ([f"- ... +{len(sorun[k]) - 40}"] if len(sorun[k]) > 40 else []) + [""]
if not any(sorun.values()):
    out.append("Sorun yok.")
rapor = "\n".join(out)
print(rapor)
if "--yaz" in sys.argv:
    (KOK / "lint_raporu.md").write_text(rapor + "\n", encoding="utf-8")
sys.exit(1 if sorun["gizli"] or sorun["kirik"] else 0)
