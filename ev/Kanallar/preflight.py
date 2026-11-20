"""Uretim oncesi on kontrol (salt okunur). Kullanim: python preflight.py [--json]

Iki uretim hattinin ortak servislerini paralel kontrol eder, Turkce OK/FAIL tablosu basar.
Hicbir servisi baslatmaz/durdurmaz; YouTube'a tek bir istek atar. Cikis kodu: kritik hepsi OK ise 0.
"""
import concurrent.futures as cf
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests

HOME = Path.home()
SCRIPTS = HOME / ".gemini" / "scripts"
YT_TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo", kararli herkese acik video
OK, WARN, FAIL, INFO = "OK", "UYARI", "FAIL", "BILGI"


def res(name, status, detail, fix="", critical=True):
    return {"ad": name, "durum": status, "detay": detail, "yapilacak": fix, "kritik": critical}


def _cfg(name):
    return json.loads((SCRIPTS / name).read_text(encoding="utf-8"))


def listening(port, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def http_check(name, url, fix, headers=None, ok_any_http=True, critical=True, timeout=6):
    t = time.time()
    try:
        r = requests.get(url, headers={**(headers or {}), "Accept-Encoding": "identity"}, timeout=timeout)
    except requests.exceptions.ContentDecodingError:
        return res(name, OK, "yanit geldi (govde cozulemedi)", "", critical)
    except Exception as e:
        return res(name, FAIL, f"ulasilamadi: {type(e).__name__}", fix, critical)
    ms = int((time.time() - t) * 1000)
    if r.ok or (ok_any_http and r.status_code in (401, 403, 404, 405)):
        return res(name, OK, f"HTTP {r.status_code}, {ms} ms", "", critical)
    return res(name, FAIL, f"HTTP {r.status_code}", fix, critical)


def chk_pocket():
    return http_check("Pocket TTS :7863", "http://127.0.0.1:7863/api/info",
                      r"Start-Pocket.ps1 calistir (C:\Users\meteh\codex-repo-tests\voice-lab\Start-Pocket.ps1)",
                      ok_any_http=False)


def chk_flash():
    # 11-18: 9router devri bitti (kullanici); tek LLM yolu yerel gemweb :8790. Kredi harcamamak icin yalniz /v1/models.
    name = "gemweb :8790 (hydrogen)"
    t = time.time()
    try:
        r = requests.get("http://127.0.0.1:8790/v1/models", timeout=10)
    except Exception as e:
        return res(name, FAIL, f"ulasilamadi: {type(e).__name__}",
                   "gemweb sunucusu kapali: yoneten oturuma haber ver (kendin yeniden baslatma)")
    ms = int((time.time() - t) * 1000)
    ids = [m.get("id") for m in (r.json().get("data") or [])] if r.ok else []
    if "gemini-4-hydrogen" in ids:
        return res(name, OK, f"gemini-4-hydrogen listede, {ms} ms")
    return res(name, FAIL, f"HTTP {r.status_code}, hydrogen yok", "gemweb_kullanim.md'ye bak")


def chk_gpt():
    # Uretim cagrisi uzun (~120 sn) -> burada yalniz erisilebilirlik: herhangi bir HTTP yaniti yeter.
    return http_check("GPT gateway VDS :8765", "http://100.104.78.117:8765/v1/models",
                      "Tailscale acik mi / VDS'de :8765 servisi calisiyor mu bak; olmazsa Flash-low'a gec",
                      timeout=8)


def chk_glabs():
    try:
        base = _cfg("glabs_gateway.json").get("base_url", "http://127.0.0.1:8765").rstrip("/")
    except Exception:
        base = "http://127.0.0.1:8765"
    return http_check("G-Labs API :8765", base + "/",
                      "G-Labs uygulamasini/API'sini ac (127.0.0.1:8765); gorsel uretimi (ZERO PULSE) icin gerekli")


def chk_searx():
    base = (os.environ.get("DOCUMENTARY_SEARXNG") or "http://100.104.78.117:8888").rstrip("/")
    name = f"SearXNG {base}"
    fix = "VDS'te `ssh root@100.104.78.117 docker start searxng` (Tailscale acik mi?); yedek: Docker Desktop + `docker start searxng`"
    try:
        r = requests.get(base + "/search", timeout=12,
                         params={"q": "Hyatt Regency walkway collapse", "categories": "images", "format": "json"})
        j = r.json()
    except Exception as e:
        return res(name, FAIL, f"ulasilamadi: {type(e).__name__}", fix)
    n = len(j.get("results", []))
    susp = sorted({u[0] if isinstance(u, list) else str(u) for u in j.get("unresponsive_engines", [])})
    detail = f"{n} gorsel sonuc; askida: {', '.join(susp) if susp else 'yok'}"
    if n == 0:
        return res(name, FAIL, detail, "Motorlar askida; birkac dakika bekle veya `docker restart searxng`")
    return res(name, WARN if susp else OK, detail, "Askidaki motorlar kendiliginden doner" if susp else "")


def chk_pot():
    name = "bgutil PO-token :4416"
    try:
        if requests.get("http://127.0.0.1:4416/ping", timeout=3).ok:
            return res(name, OK, "ping yanit verdi", critical=False)
    except Exception:
        pass
    return res(name, WARN, "kapali", "Sorun degil: hat ilk YouTube isteginde kendisi baslatir (sources.ensure_pot_server)",
               critical=False)


def chk_firefox():
    name = "Firefox profili"
    exe = Path(r"C:\Program Files\Mozilla Firefox\firefox.exe")
    prof = Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
    cookies = list(prof.glob("*/cookies.sqlite")) if prof.is_dir() else []
    if not exe.is_file() and not shutil.which("firefox"):
        return res(name, FAIL, "Firefox kurulu degil", "Firefox kur ve YouTube'a giris yap")
    if not cookies:
        return res(name, FAIL, "cookies.sqlite yok", "Firefox'u bir kez ac, YouTube'a giris yap")
    return res(name, OK, f"{len(cookies)} profilde cookies.sqlite var")


def chk_youtube():
    name = "YouTube cerezleri (1 istek)"
    os.environ["DOCUMENTARY_YT_COOKIES_BROWSER"] = "firefox"
    sys.path.insert(0, str(SCRIPTS))
    t = time.time()
    try:
        import yt_dlp
        from documentary_materials import sources, yt_gate

        def fn():
            opts = {"quiet": True, "no_warnings": True, "skip_download": True, "socket_timeout": 15,
                    "retries": 0, "extractor_retries": 0, **sources._yt_common(),
                    "extractor_args": sources.YOUTUBE_ARGS}
            opts["sleep_interval_requests"] = 0
            with yt_dlp.YoutubeDL(opts) as y:
                return y.extract_info(YT_TEST_URL, download=False)

        # gate.call 429/bot hatasinda yeniden dener (BLOCK_RETRIES); tek istek icin kapiyi bir kez gec.
        yt_gate.BLOCK_RETRIES = 0
        info = yt_gate.call("preflight", fn)
        return res(name, OK, f"metadata alindi ({info.get('title', '?')}), {int(time.time() - t)} sn")
    except Exception as e:
        msg = str(e)
        low = msg.lower()
        if any(k in low for k in ("sign in", "not a bot", "cookies", "429", "403", "too many")):
            return res(name, FAIL, msg.splitlines()[0][:110], "Firefox'ta YouTube oturumunu ac")
        return res(name, FAIL, f"{type(e).__name__}: {msg.splitlines()[0][:100] if msg else ''}",
                   "Firefox'ta YouTube oturumunu ac; surmuyorsa yt-dlp/ag baglantisini kontrol et")


def chk_machine():
    out = []
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("tot", ctypes.c_ulonglong),
                        ("avail", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                        ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
        m = MS()
        m.l = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        gb = m.avail / 2**30
        out.append(res("Bos RAM", WARN if gb < 6 else OK, f"{gb:.1f} GB / {m.tot / 2**30:.0f} GB",
                       "Gereksiz sureclari kapat; ayni anda film sayisini dusur" if gb < 6 else "", critical=False))
    except Exception as e:
        out.append(res("Bos RAM", WARN, f"olculemedi: {e}", critical=False))
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=8)
        free, tot = [int(x) for x in r.stdout.strip().splitlines()[0].split(",")]
        out.append(res("Bos GPU bellegi", WARN if free < 1000 else OK, f"{free} MB / {tot} MB",
                       "GPU'yu kullanan sureci kapat (Sopro GPU'da calismamali)" if free < 1000 else "",
                       critical=False))
    except Exception as e:
        out.append(res("Bos GPU bellegi", WARN, f"nvidia-smi yok/hata: {type(e).__name__}", critical=False))
    free = shutil.disk_usage("C:\\").free / 2**30
    out.append(res("Bos disk C:", WARN if free < 30 else OK, f"{free:.0f} GB",
                   "Teslim edilmis ciktilari / gecici klasorleri temizle" if free < 30 else "", critical=False))
    for label, port in (("Uretim koprusu :8099", 8099), ("Test koprusu :8199", 8199)):
        up = listening(port)
        out.append(res(label, INFO, "dinliyor" if up else "dinlemiyor", critical=False))
    return out


def chk_leftovers():
    # Onceki isten arkada kalan ffmpeg/ffprobe ve render chrome'u (headless) RAM yer; kullanicinin kendi Chrome'u sayilmaz.
    name = "Arkada kalan ffmpeg/chrome"
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='ffmpeg.exe' or Name='ffprobe.exe' or Name='chrome.exe' "
          "or Name='chrome-headless-shell.exe'\" | ForEach-Object { [pscustomobject]@{n=$_.Name; id=$_.ProcessId; "
          "mb=[int]($_.WorkingSetSize/1MB); age=[int]((Get-Date)-$_.CreationDate).TotalMinutes; "
          "h=[bool]($_.CommandLine -match '--headless')} } | ConvertTo-Json -Compress")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=20)
        rows = json.loads(r.stdout or "[]")
    except Exception as e:
        return res(name, WARN, f"olculemedi: {type(e).__name__}", critical=False)
    rows = [rows] if isinstance(rows, dict) else rows
    left = [p for p in rows if p["n"] in ("ffmpeg.exe", "ffprobe.exe", "chrome-headless-shell.exe") or p["h"]]
    if not left:
        return res(name, OK, "yok", critical=False)
    ids = ",".join(str(p["id"]) for p in left)
    busy = listening(8099) or listening(8199)
    detail = (f"{len(left)} surec, {sum(p['mb'] for p in left)} MB, en eskisi {max(p['age'] for p in left)} dk"
              + ("; kopru calisiyor, suren ise ait olabilir" if busy else ""))
    return res(name, WARN, detail, f"Is calismiyorsa kapat: Stop-Process -Id {ids}", critical=False)


def main():
    t0 = time.time()
    checks = [chk_pocket, chk_flash, chk_gpt, chk_glabs, chk_searx, chk_pot, chk_firefox, chk_youtube, chk_machine,
              chk_leftovers]
    results = []
    with cf.ThreadPoolExecutor(len(checks)) as ex:
        futs = [ex.submit(c) for c in checks]
        for c, f in zip(checks, futs):
            try:
                r = f.result(timeout=60)
            except Exception as e:
                r = res(c.__name__, FAIL, f"kontrol coktu: {type(e).__name__}: {e}")
            results.extend(r if isinstance(r, list) else [r])
    total = time.time() - t0
    failed = [r for r in results if r["kritik"] and r["durum"] == FAIL]
    if "--json" in sys.argv:
        print(json.dumps({"sure_sn": round(total, 1), "tamam": not failed, "sonuclar": results},
                         ensure_ascii=False, indent=2))
    else:
        w = max(len(r["ad"]) for r in results)
        for r in results:
            print(f"[{r['durum']:<5}] {r['ad']:<{w}}  {r['detay']}")
            if r["yapilacak"] and r["durum"] in (FAIL, WARN):
                print(f"        -> {r['yapilacak']}")
        print(f"\nSure: {total:.1f} sn. " + ("Kritik kontroller TAMAM." if not failed else
              "KRITIK HATA: " + ", ".join(r["ad"] for r in failed)))
    ek = 0
    if "--json" not in sys.argv:  # makine ek kontrolleri (commit limiti, disk, yetim surec; ~4 sn)
        import subprocess
        print("\n-- makine ek kontrolleri --", flush=True)
        ek = subprocess.run([sys.executable, str(Path(__file__).with_name("preflight_ek.py"))]).returncode
    sys.exit(1 if failed or ek else 0)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
