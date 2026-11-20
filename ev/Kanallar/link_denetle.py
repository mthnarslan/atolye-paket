import time
"""Arastirma raporu denetleyici: linkler canli mi, alinti ve sayilar sayfada gecıyor mu.

Kullanim:
  python C:/Users/meteh/Kanallar/link_denetle.py rapor.md [--json cikti.json]
  ... | python link_denetle.py -

Her paragraf (bos satirla ayrilan blok ya da tablo satiri) icindeki URL'ler cekilir.
- Link: 2xx/3xx = canli; acilmazsa Wayback'e bakilir -> "curumus (arsivde var)" ya da "bulunamadi".
  403/429 gibi bot engeli "engelli" sayilir (uydurma demek degil).
- Alinti: paragraftaki "..." / “...” icindeki >=4 kelimelik metin, ayni paragraftaki sayfalarin
  metninde birebir (ya da >=%85 benzer) geciyor mu. Ceviri alinti tutmaz: alinti orijinal dilde yazilmali.
- Sayi: paragraftaki % / $ / ondalikli sayilar sayfa metninde geciyor mu (uyari, hata degil).
Reddit linkleri api.pullpush.io ile okunur. Cikis kodu: 0 temiz, 1 bulunamayan link ya da tutmayan alinti.
"""
import sys, re, json, subprocess, html, argparse, difflib, urllib.request, urllib.parse, ssl
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
URL_RE = re.compile(r"https?://[^\s<>\"'`)\]|]+")
QUOTE_RE = re.compile(r"[\"“”„«]([^\"“”„«»]{12,400})[\"“”»]")
NUM_RE = re.compile(r"(?:\$\s?\d[\d.,]*|\d[\d.,]*\s?%|\d+[.,]\d+)")
CTX = ssl.create_default_context()


def get(url, timeout=25):
    for i in range(3):
        try:
            return _get(url, timeout)
        except urllib.error.HTTPError as e:
            if e.code not in (422, 520, 521, 522, 524) or i == 2:
                raise
            time.sleep(8 * (i + 1))


def _get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en,tr;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read(4_000_000).decode("utf-8", "replace"), r.geturl()


def curl(url, timeout=25):
    """Python'u engelleyen (TLS parmak izi) siteler icin curl yedegi."""
    r = subprocess.run(["curl", "-sL", "--compressed", "-A", UA, "--max-time", str(timeout),
                        "-w", "\n%{http_code} %{url_effective}", url],
                       capture_output=True, timeout=timeout + 5)
    body, _, tail = r.stdout.decode("utf-8", "replace").rpartition("\n")
    code, _, final = tail.partition(" ")
    return int(code or 0), body, final


def soft404(asked, final, raw):
    a, f = urllib.parse.urlparse(asked), urllib.parse.urlparse(final)
    ap_, fp = a.path.strip("/"), f.path.strip("/")
    if ap_ and ap_ != fp and (not fp or ap_.startswith(fp + "/")):
        return True  # derin linkten ana sayfaya / ust klasore (ay arsivi vb.) yonlendi
    title = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
    return bool(title and re.search(r"not found|404|page doesn.t exist|bulunamad", title.group(1), re.I))


def to_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return html.unescape(raw)


def norm(s):
    s = s.lower()
    s = s.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "\u00a0": " "}))
    return re.sub(r"\s+", " ", s).strip()


def reddit(url):
    m = re.search(r"/comments/([a-z0-9]+)", url)
    if not m:
        return None
    pid = m.group(1)
    base = "https://api.pullpush.io/reddit/search/"
    _, a, _ = get(f"{base}submission/?ids={pid}")
    sub = json.loads(a).get("data", [])
    if not sub:
        return None
    parts = [sub[0].get("title", ""), sub[0].get("selftext", "")]
    try:
        _, c, _ = get(f"{base}comment/?link_id={pid}&size=100")
        parts += [x.get("body", "") for x in json.loads(c).get("data", [])]
    except Exception:
        pass
    return "\n".join(parts)


def hn(url):
    m = re.search(r"news\.ycombinator\.com/item\?id=(\d+)", url)
    if not m:
        return None
    _, a, _ = get(f"https://hn.algolia.com/api/v1/items/{m.group(1)}")
    parts = []
    def walk(n):
        parts.append((n.get("title") or "") + " " + to_text(n.get("text") or ""))
        for c in n.get("children") or []:
            walk(c)
    walk(json.loads(a))
    return "\n".join(parts)


def wayback(url):
    try:
        _, a, _ = get("https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe=""), 20)
        snap = json.loads(a).get("archived_snapshots", {}).get("closest")
        return snap.get("url") if snap and snap.get("available") else None
    except Exception:
        return None


def fetch(url):
    """-> dict(durum, kod, metin)"""
    url = url.rstrip(".,;:")
    try:
        if re.search(r"https?://(www.|old.)?reddit.com", url) or "news.ycombinator.com" in url:
            t = reddit(url) if "reddit.com" in url else hn(url)
            if t is not None:
                return {"durum": "canli", "kod": "api", "metin": t}
        try:
            code, raw, final = get(url)
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429, 503, 520, 521, 522, 524):
                raise
            code, raw, final = curl(url)
            if code >= 400:
                raise urllib.error.HTTPError(url, code, "curl", None, None)
        if soft404(url, final, raw):
            code = "soft404"
        else:
            return {"durum": "canli", "kod": code, "metin": to_text(raw)}
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        code = type(e).__name__
    if code in (401, 403, 419, 429, 999):
        return {"durum": "engelli", "kod": code, "metin": ""}
    snap = wayback(url)
    if snap:
        try:
            _, raw, _ = get(snap)
            return {"durum": "curumus", "kod": code, "metin": to_text(raw), "arsiv": snap}
        except Exception:
            return {"durum": "curumus", "kod": code, "metin": "", "arsiv": snap}
    return {"durum": "bulunamadi", "kod": code, "metin": ""}


def found(quote, text):
    q, t = norm(quote), norm(text)
    if not q or not t:
        return False, 0.0
    if q in t:
        return True, 1.0
    sm = difflib.SequenceMatcher(None, t, q, autojunk=False)
    m = sm.find_longest_match(0, len(t), 0, len(q))
    # en uzun eslesmenin cevresinde alinti boyunda pencere
    start = max(0, m.a - m.b)
    win = t[start:start + len(q) + 20]
    r = difflib.SequenceMatcher(None, win, q, autojunk=False).ratio()
    return r >= 0.85, round(r, 2)


def num_variants(n):
    core = re.sub(r"[$%\s]", "", n)
    vs = {core, core.replace(",", "."), core.replace(".", ",")}
    return {v for v in vs if v}


def blocks(text):
    out = []
    for b in re.split(r"\n\s*\n", text):
        lines = b.splitlines()
        if any(l.strip().startswith("|") for l in lines):
            out += [l for l in lines if l.strip()]
        else:
            out.append(b)
    return [b for b in out if URL_RE.search(b)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rapor")
    ap.add_argument("--json")
    a = ap.parse_args()
    text = sys.stdin.read() if a.rapor == "-" else open(a.rapor, encoding="utf-8").read()
    bl = blocks(text)
    urls = sorted({u.rstrip(".,;:") for b in bl for u in URL_RE.findall(b)})
    with ThreadPoolExecutor(int(__import__("os").environ.get("LINK_WORKERS", "8"))) as ex:
        pages = dict(zip(urls, ex.map(fetch, urls)))

    hata, uyari, sonuc = 0, 0, {"linkler": {}, "alintilar": [], "sayilar": []}
    print(f"== Linkler ({len(urls)}) ==")
    for u in urls:
        p = pages[u]
        isaret = {"canli": "OK ", "engelli": "ENG", "curumus": "ARS", "bulunamadi": "YOK"}[p["durum"]]
        if p["durum"] == "bulunamadi":
            hata += 1
        print(f"[{isaret}] {p['kod']} {u}" + (f"  -> {p['arsiv']}" if p.get("arsiv") else ""))
        sonuc["linkler"][u] = {k: v for k, v in p.items() if k != "metin"}

    print("== Alintilar ==")
    for b in bl:
        bu = [u.rstrip(".,;:") for u in URL_RE.findall(b)]
        metin = "\n".join(pages[u]["metin"] for u in bu)
        okunan = any(pages[u]["metin"] for u in bu)
        for q in QUOTE_RE.findall(b):
            if len(q.split()) < 4 or URL_RE.search(q):
                continue
            if not okunan:
                print(f"[?  ] okunamadi: \"{q[:80]}\"")
                continue
            ok, r = found(q, metin)
            if not ok:
                hata += 1
            print(f"[{'OK ' if ok else 'YOK'}] {r} \"{q[:80]}\"")
            sonuc["alintilar"].append({"alinti": q, "ok": ok, "benzerlik": r, "urller": bu})
        if okunan:
            nt = norm(metin)
            for n in set(NUM_RE.findall(b)):
                if any(v in nt for v in num_variants(n)):
                    continue
                uyari += 1
                print(f"[SAY] sayfada yok: {n.strip()}  ({bu[0][:70]})")
                sonuc["sayilar"].append({"sayi": n.strip(), "urller": bu})

    print(f"== Ozet: {len(urls)} link, hata {hata}, sayi uyarisi {uyari} ==")
    if a.json:
        json.dump(sonuc, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.exit(1 if hata else 0)


if __name__ == "__main__":
    main()
