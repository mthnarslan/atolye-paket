import argparse, json, os, sys, time, hashlib, urllib.parse
from pathlib import Path
import requests

BASE = Path(r"C:\Users\meteh\Kanallar\ortak")
STATE = BASE / "state"
CACHE = BASE / "cache" / "commons"
LOCK = STATE / "commons.lock"
LAST = STATE / "commons.last_request"
UA = "W2-Commons-Downloader/1.0 (general project contact: Wikimedia Commons project page)"
WIDTHS = (960, 1280, 1920)
MAX_TRIES = 5

def _wait_turn():
    STATE.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - LOCK.stat().st_mtime > 10: LOCK.unlink()  # olen surecin kilidi
            except FileNotFoundError: pass
            time.sleep(0.2)
    try:
        now = time.time()
        try: last = float(LAST.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError): last = 0
        delay = 1.0 - (now - last)
        if delay > 0: time.sleep(delay)
        LAST.write_text(str(time.time()), encoding="utf-8")
    finally:
        try: LOCK.unlink()
        except FileNotFoundError: pass

def _request(url, **kwargs):
    for attempt in range(MAX_TRIES):
        _wait_turn()
        r = requests.get(url, headers={"User-Agent": UA}, timeout=45, **kwargs)
        if r.status_code not in (429, 503): return r
        ra = r.headers.get("Retry-After")
        try: delay = float(ra)
        except (TypeError, ValueError): delay = 2 ** attempt
        if delay > 60:  # uzun ceza: bekleyip kanali kilitleme, bu dosyayi atla
            raise RuntimeError(f"Commons {r.status_code} Retry-After {ra}s: {url[:80]}")
        time.sleep(delay)
    return r

def _api_file(name, width=None):
    prm = {"action":"query","format":"json","prop":"imageinfo","iiprop":"url","titles":"File:" + name.removeprefix("File:")}
    if width: prm["iiurlwidth"] = str(width)
    r = _request("https://commons.wikimedia.org/w/api.php", params=prm)
    r.raise_for_status()
    pages = r.json()["query"]["pages"]
    p = next(iter(pages.values()))
    if "imageinfo" not in p: raise ValueError("Commons dosyasi bulunamadi")
    ii = p["imageinfo"][0]
    return p["title"], (ii.get("thumburl") or ii["url"]) if width else ii["url"]

def _resolve(value, original=False, width=1280):
    w = min((x for x in WIDTHS if x >= width), default=WIDTHS[-1])
    tw = None if original else w  # API thumburl: SVG/TIFF->png ve kucuk orijinali dogru verir
    if value.startswith("File:") or ("://" not in value and "/" not in value):
        title, u = _api_file(value, tw); return title, u
    elif "commons.wikimedia.org/wiki/" in value or "commons.wikimedia.org/w/index.php" in value:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(value).query)
        title = q.get("title", [""])[0] or urllib.parse.unquote(urllib.parse.urlparse(value).path.rsplit("/",1)[-1]).replace("_", " ")
        title, u = _api_file(title.removeprefix("File:"), tw); return title, u
    else:
        title, original_url = urllib.parse.unquote(value.rsplit("/",1)[-1]), value
    if original: return title, original_url
    if "upload.wikimedia.org" in original_url:
        parts = original_url.split("/commons/",1)
        if len(parts) == 2:
            fn = parts[1].rsplit("/",1)[-1]
            return title, "https://upload.wikimedia.org/wikipedia/commons/thumb/" + parts[1].rsplit("/",1)[0] + f"/{w}px-{fn}"
    return title, original_url

def indir(url_ya_da_dosya_adi, hedef_klasor, genislik=1280, original=False):
    title, url = _resolve(url_ya_da_dosya_adi, original, genislik)
    key = hashlib.sha256(url.encode()).hexdigest()
    CACHE.mkdir(parents=True, exist_ok=True); Path(hedef_klasor).mkdir(parents=True, exist_ok=True)
    ext = Path(urllib.parse.urlparse(url).path).suffix or ".bin"
    cached = CACHE / (key + ext)
    if not cached.exists():
        r = _request(url); r.raise_for_status(); cached.write_bytes(r.content)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in title.removeprefix("File:"))
    out = Path(hedef_klasor) / safe
    if out.suffix.lower() != ext.lower(): out = out.with_suffix(ext)
    if not out.exists(): out.write_bytes(cached.read_bytes())
    return str(out)

def main():
    p=argparse.ArgumentParser(); p.add_argument("kaynak", nargs="?"); p.add_argument("--cikti", required=True); p.add_argument("--genislik", type=int, default=1280); p.add_argument("--orijinal", action="store_true"); p.add_argument("--liste")
    a=p.parse_args(); items=[x.strip() for x in open(a.liste, encoding="utf-8") if x.strip()] if a.liste else [a.kaynak]
    for x in items:
        try: print(indir(x, a.cikti, a.genislik, a.orijinal), flush=True)
        except Exception as e: print(f"ERROR {x}: {e}", file=sys.stderr, flush=True)
if __name__ == "__main__": main()
