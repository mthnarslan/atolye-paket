"""resim_bul: beat basina GERCEK foto bul (tum kanallar).
  python resim_bul.py beats.json --cikti DIR [--aday 12] [--min-gen 900] [--paralel 6]
beats.json: [{"id":"b01","ne":"ne gorunmeli (kisa)","sorgular":["...",...]}]  (sorgular yoksa 'ne' aranir)
Akis: SearXNG gorsel arama (VDS, yoksa yerel) -> stok/filigran sitesi ele -> paralel indir -> boyut/kopya kontrol
-> numarali kontak sayfa -> Gemini (gemweb) en iyi gercek fotoyu secer (filigran/modern/cizim/yazi ceza).
Cikti: DIR/<id>.jpg (en iyi), DIR/<id>_2.jpg (yedek), DIR/<id>_sheet.jpg, DIR/rapor.json. Puan<6 = 'ZAYIF' (elle bak / sorgu degistir)."""
import argparse, hashlib, io, json, os, re, sys, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import gemweb

SX = [os.environ.get("DOCUMENTARY_SEARXNG", "http://100.104.78.117:8888"), "http://127.0.0.1:8888"]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}
# filigranli stok/ajans siteleri: SISTEM kurali, lisans yazisi temizlenmez -> hic alma
KARA = re.compile(r"gettyimages|alamy|shutterstock|dreamstime|istockphoto|depositphotos|123rf|stock\.adobe|imago-images|akg-images|ullsteinbild|"
                  r"picture-alliance|bridgemanimages|agefotostock|mauritius-images|sz-photo|bpk-images|granger|mediastorehouse|meisterdrucke|"
                  r"pond5|storyblocks|vecteezy|freepik|etsy|ebay|amazon|lookandlearn|topfoto|mary ?evans|superstock|interfoto|keystone-sda", re.I)
TERCIH = re.compile(r"wikimedia|wikipedia|bundesarchiv|europeana|loc\.gov|archives\.gov|nationaalarchief|gallica|deutsche-digitale|"
                    r"saarland|sr\.de|sr-mediathek|saarbruecker|landesarchiv|bpb\.de|dhm\.de|hdg\.de|archive\.org", re.I)

def ara(q):
    for b in SX:
        try:
            r = requests.get(f"{b}/search", params={"q": q, "categories": "images", "format": "json"}, timeout=40)
            if r.ok: return r.json().get("results", [])
        except requests.RequestException: pass
    return []

def gen(res):
    m = re.match(r"\s*(\d+)\s*[x××]\s*(\d+)", res or "")
    return (int(m[1]), int(m[2])) if m else (0, 0)

def adaylar(beat, n, min_gen):
    gor, liste = set(), []
    for qi, q in enumerate(beat.get("sorgular") or [beat["ne"]]):
        for ri, r in enumerate(ara(q)):
            u = r.get("img_src") or ""
            if not u.startswith("http") or u in gor or KARA.search(u + " " + (r.get("url") or "")): continue
            gor.add(u); w, h = gen(r.get("resolution"))
            if w and (w < min_gen * .8 or w < h * .6): continue  # kucuk ya da cok dikey
            p = ri + 3 * qi - (8 if TERCIH.search(u) else 0) - (4 if w >= min_gen else 0)
            liste.append((p, u, r.get("title", "")[:120], r.get("url", "")))
        time.sleep(.5)
    liste.sort()
    return liste[:n * 2]

def indir(u):
    try:
        if "upload.wikimedia.org" in u and "/thumb/" not in u:  # orijinal 429 verir: standart thumb iste
            p = u.split("/commons/")[-1]; fn = p.split("/")[-1]
            u = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{p}/1920px-{fn}"
        r = requests.get(u, headers=UA, timeout=25)
        if not r.ok or len(r.content) < 25000: return None
        im = Image.open(io.BytesIO(r.content)); im.load(); im = ImageOps.exif_transpose(im).convert("RGB")
        return im
    except Exception:
        return None

def ahash(im):
    g = im.convert("L").resize((16, 16)); px = list(g.getdata()); m = sum(px) / len(px)
    return sum(1 << i for i, v in enumerate(px) if v > m)

def sheet(ims, yol):
    W, H = 640, 400; c = 3; r = (len(ims) + c - 1) // c
    S = Image.new("RGB", (W * c, H * r), (30, 30, 30)); d = ImageDraw.Draw(S)
    try: f = ImageFont.truetype("arialbd.ttf", 56)
    except OSError: f = ImageFont.load_default()
    for i, im in enumerate(ims):
        t = ImageOps.contain(im, (W - 8, H - 8)); x, y = (i % c) * W, (i // c) * H
        S.paste(t, (x + (W - t.width) // 2, y + (H - t.height) // 2))
        d.rectangle([x, y, x + 74, y + 66], fill=(220, 30, 30)); d.text((x + 14, y + 2), str(i + 1), fill="white", font=f)
    S.save(yol, quality=85)

def is_(beat, a):
    out = a.cikti; L = adaylar(beat, a.aday, a.min_gen)
    with ThreadPoolExecutor(8) as ex: ims = list(ex.map(indir, [x[1] for x in L]))
    sec, hs = [], []
    for x, im in zip(L, ims):
        if im is None or im.width < a.min_gen * .75: continue
        h = ahash(im)
        if any(bin(h ^ k).count("1") < 20 for k in hs): continue
        hs.append(h); sec.append((x, im))
        if len(sec) >= a.aday: break
    if not sec: return {"id": beat["id"], "durum": "BULUNAMADI", "aday": 0}
    sh = os.path.join(out, f"{beat['id']}_sheet.jpg"); sheet([im for _, im in sec], sh)
    q = (f"Numbered candidate images (red numbers 1..{len(sec)}) for a history documentary shot. Needed: {beat['ne']}.\n"
         "Score each 0-10: 10 = real historical PHOTOGRAPH (or period document) clearly showing exactly that, good quality. "
         "Penalize hard: modern photo/color if historical needed, painting/drawing/illustration (unless asked), visible watermark or stock-agency logo, "
         "big overlaid text/caption/collage/TV graphics, wrong place/era, tiny/blurry. "
         'Return ONLY JSON: {"puan":{"1":7,...},"sorun":{"1":"kisa neden",...},"en_iyi":[best numbers, max 3]}')
    try: j = gemweb.sor_json(q, gorseller=[sh], zaman=240)
    except Exception as e: return {"id": beat["id"], "durum": f"GEMINI_HATA {str(e)[:80]}", "aday": len(sec)}
    puan = {int(k): float(v) for k, v in (j.get("puan") or {}).items() if str(k).isdigit()}
    sira = [int(i) for i in j.get("en_iyi") or [] if 1 <= int(i) <= len(sec)] or sorted(puan, key=puan.get, reverse=True)
    rap = {"id": beat["id"], "ne": beat["ne"], "aday": len(sec), "sec": []}
    for k, n in enumerate(sira[:2]):
        (_, u, t, page), im = sec[n - 1]
        im.save(os.path.join(out, f"{beat['id']}{'' if k == 0 else '_2'}.jpg"), quality=92)
        rap["sec"].append({"no": n, "puan": puan.get(n), "url": u, "sayfa": page, "baslik": t, "boyut": f"{im.width}x{im.height}", "sorun": (j.get("sorun") or {}).get(str(n), "")})
    rap["durum"] = "OK" if rap["sec"] and (rap["sec"][0]["puan"] or 0) >= 6 else "ZAYIF"
    return rap

def main():
    p = argparse.ArgumentParser(); p.add_argument("beats"); p.add_argument("--cikti", required=True)
    p.add_argument("--aday", type=int, default=12); p.add_argument("--min-gen", type=int, default=900); p.add_argument("--paralel", type=int, default=6)
    p.add_argument("--sadece", default=""); a = p.parse_args()
    os.makedirs(a.cikti, exist_ok=True); B = json.load(open(a.beats, encoding="utf8"))
    if a.sadece: B = [b for b in B if b["id"] in a.sadece.split(",")]
    with ThreadPoolExecutor(a.paralel) as ex: R = list(ex.map(lambda b: is_(b, a), B))
    yol = os.path.join(a.cikti, "rapor.json"); eski = {}
    if os.path.exists(yol): eski = {r["id"]: r for r in json.load(open(yol, encoding="utf8"))}
    eski.update({r["id"]: r for r in R}); json.dump(list(eski.values()), open(yol, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    for r in R: print(r["id"], r["durum"], r.get("aday"), (r.get("sec") or [{}])[0].get("puan"), (r.get("sec") or [{}])[0].get("baslik", "")[:60], flush=True)

if __name__ == "__main__":
    main()
