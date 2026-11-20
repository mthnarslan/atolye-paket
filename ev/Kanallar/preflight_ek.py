"""preflight.py'nin yakalamadigi makine kararliligi kontrolleri (SALT OKUNUR, ~3-6 sn).

Kullanim: python preflight_ek.py [--json]
Hicbir sey silmez/oldurmez/baslatmaz. Cikis kodu 1 = en az bir FAIL.
Her kontrolun dayandigi ders: beyin/ders/<ad> (detay icin RAPOR.md).
"""
import ctypes
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil

GB = 2 ** 30
OK, WARN, FAIL, INFO = "OK", "UYARI", "FAIL", "BILGI"
R = []


def add(ad, durum, detay, yap=""):
    R.append({"ad": ad, "durum": durum, "detay": detay, "yapilacak": yap})


class _MS(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("totp", ctypes.c_ulonglong),
                ("availp", ctypes.c_ulonglong), ("totpf", ctypes.c_ulonglong), ("availpf", ctypes.c_ulonglong),
                ("totv", ctypes.c_ulonglong), ("availv", ctypes.c_ulonglong), ("ext", ctypes.c_ulonglong)]


def chk_commit():
    # commit-limit-kopru-1109: fiziksel bos RAM yaniltir; WinError 1455 / brotli / mkl_malloc = commit limiti.
    m = _MS()
    m.l = ctypes.sizeof(_MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    free, lim = m.availpf / GB, m.totpf / GB  # availpf = commit limiti - taahhut edilen
    used = lim - free
    d = f"commit {used:.1f}/{lim:.1f} GB kullanimda, bos {free:.1f} GB; fiziksel bos {m.availp / GB:.1f} GB"
    if free < 4:
        add("Commit (bos sanal bellek)", FAIL, d, "Kopru/clean_overlay/test iscilerini kapat (ders: commit-limit-kopru-1109)")
    elif free < 12:
        add("Commit (bos sanal bellek)", WARN, d, "Yeni film/GPU temizligi baslatma; kopru private'i buyukse yeniden baslat")
    else:
        add("Commit (bos sanal bellek)", OK, d)
    if lim < 50:
        add("Commit limiti (pagefile)", WARN, f"limit {lim:.1f} GB (11-09'da 65 GB'di; pagefile yeniden baslatmada kuculur)",
            "Parti oncesi 3 isci x 5-15 GB tepe sigmayabilir: es zamanli film sayisini dusur veya pagefile alt sinirini yukselt (kullanici karari)")
    else:
        add("Commit limiti (pagefile)", OK, f"limit {lim:.1f} GB")


def chk_disk():
    f = shutil.disk_usage("C:\\").free / GB
    d = f"C: bos {f:.0f} GB"
    if f < 20:
        add("Disk C: (esikli)", FAIL, d, "Ham sources/pre_repair/eski testbench kopyalarini temizle (RAPOR.md)")
    elif f < 70:
        add("Disk C: (esikli)", WARN, d, "<70 GB: QLC SSD yazma gecikmesi artar (pc-kasma-iobit-ssd-1110)")
    else:
        add("Disk C: (esikli)", OK, d)
    # yazma gecikmesi 1 sn ornek
    try:
        a = psutil.disk_io_counters()
        time.sleep(1.0)
        b = psutil.disk_io_counters()
        wc = b.write_count - a.write_count
        wt = b.write_time - a.write_time
        lat = wt / wc if wc else 0.0
        d = f"yazma {wc} islem/sn, ort. gecikme {lat:.0f} ms (psutil write_time, yaklasik)"
        add("Disk yazma gecikmesi", WARN if lat > 100 else OK, d,
            "Disk yogun: IObit/Defender/indirme sureclerine bak" if lat > 100 else "")
    except Exception as e:
        add("Disk yazma gecikmesi", WARN, f"olculemedi: {type(e).__name__}")


def _cmd(p):
    try:
        return " ".join(p.cmdline())[:160]
    except Exception:
        return ""


def chk_processes():
    procs = []
    for p in psutil.process_iter(["pid", "name", "create_time"]):
        try:
            mi = p.memory_info()
            procs.append((p, mi.private if hasattr(mi, "private") else mi.vms, mi.rss))
        except Exception:
            pass
    now = time.time()
    # 1) kopru private bytes (kopru-bellek-sismesi-1108: >8 GB yeniden baslat)
    ports = {}
    try:
        for c in psutil.net_connections("tcp"):
            if c.status == "LISTEN" and c.laddr.port in (8099, 8199):
                ports[c.laddr.port] = c.pid
    except Exception:
        pass
    for port, pid in ports.items():
        try:
            pr = psutil.Process(pid)
            priv = pr.memory_info().private / GB
            age = (now - pr.create_time()) / 3600
            d = f":{port} pid {pid} private {priv:.1f} GB, yas {age:.1f} sa"
            add(f"Kopru :{port} private", WARN if priv > 8 else OK, d,
                "Asama 3 bittiyse ve drive.py yoksa kopruyu ayni env ile yeniden baslat (ders: commit-limit-kopru-1109)" if priv > 8 else "")
        except Exception as e:
            add(f"Kopru :{port} private", WARN, f"olculemedi: {type(e).__name__}")
    # 2) 3 GB ustu private tutan python/node (yetim/sizinti adayi), bilinen uretim surecleri etiketli
    big = [(p, pv) for p, pv, rs in procs if pv > 3 * GB]
    if big:
        for p, pv in sorted(big, key=lambda x: -x[1])[:5]:
            nm = p.info["name"]
            add("Buyuk surec (>3 GB private)", WARN if nm.lower().startswith(("python", "node", "ffmpeg")) else INFO,
                f"{nm} pid {p.info['pid']} {pv / GB:.1f} GB, yas {(now - p.info['create_time']) / 3600:.1f} sa: {_cmd(p)[:90]}")
    else:
        add("Buyuk surec (>3 GB private)", OK, "yok")
    # 3) yetim adaylari: bilinen is betikleri / cocuklar
    pat = re.compile(r"clean_overlay|gaia_finish|lm_render|lm_run|heavy_replay|model_cycle|propainter|relaunch_watch|measure_memory", re.I)
    ff = []
    orph = []
    for p, pv, rs in procs:
        try:
            nm = p.info["name"].lower()
            if nm in ("ffmpeg.exe", "ffprobe.exe", "chrome-headless-shell.exe"):
                ff.append((p, rs))
            elif nm.startswith(("python", "pythonw")) and pat.search(_cmd(p)):
                par = p.parent()
                orph.append((p, pv, par is None))
        except Exception:
            pass
    if orph:
        for p, pv, noparent in orph:
            add("Is betigi sureci", WARN if noparent else INFO,
                f"pid {p['pid'] if isinstance(p, dict) else p.info['pid']} private {pv / GB:.1f} GB, "
                f"{'ATA SUREC YOK (yetim olabilir)' if noparent else 'ata var'}: {_cmd(p)[:90]}",
                "Is calismiyorsa py-spy dump ile bak; oldurme karari sende" if noparent else "")
    else:
        add("Is betigi sureci", OK, "clean_overlay/gaia_finish/lm_*/test betigi calismiyor")
    old = [(p, rs) for p, rs in ff if now - p.info["create_time"] > 1800]
    add("Eski ffmpeg/headless-chrome (>30 dk)", WARN if old else OK,
        f"{len(old)} surec, {sum(r for _, r in old) / 2**20:.0f} MB" if old else "yok",
        "Kopru yoksa yetim: Stop-Process -Id " + ",".join(str(p.info["pid"]) for p, _ in old) if old else "")
    # 4) takili IObit UninstallMonitor / tek cekirdek %99
    names = {p.info["name"].lower() for p, _, _ in procs}
    if "uninstallmonitor.exe" in names:
        add("IObit UninstallMonitor", FAIL, "calisiyor (pc-kasma-iobit-ssd-1110: 1 cekirdek %99 + disk G/C)",
            "Yonetici olarak sonlandir / IObit Uninstaller'i kaldir")
    else:
        add("IObit UninstallMonitor", OK, "calismiyor")
    # 5) CPU hirsizi (1 sn ornek)
    for p, _, _ in procs:
        try:
            p.cpu_percent(None)
        except Exception:
            pass
    time.sleep(1.0)
    hot = []
    for p, _, _ in procs:
        try:
            c = p.cpu_percent(None)
            if c >= 90 and p.info["pid"] not in (0, 4):
                hot.append((c, p.info["name"], p.info["pid"]))
        except Exception:
            pass
    ncpu = psutil.cpu_count()
    add("CPU hirsizi (>=90% bir cekirdek)", WARN if hot else OK,
        ", ".join(f"{n}:{pid} %{c:.0f}" for c, n, pid in sorted(hot, reverse=True)[:5]) + f" (cekirdek {ncpu})" if hot else "yok",
        "Uretim disi surec ise nedenini ara" if hot else "")
    return ports


def chk_gpu(ports):
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=6)
        used, tot, util = [int(x) for x in r.stdout.strip().splitlines()[0].split(",")]
    except Exception as e:
        add("GPU kilit/kullanim", WARN, f"nvidia-smi: {type(e).__name__}")
        return
    cl = [p for p in psutil.process_iter(["name"]) if p.info["name"].lower().startswith("python") and "clean_overlay" in _cmd(p)]
    d = f"GPU {used}/{tot} MB, kullanim %{util}, clean_overlay sureci {len(cl)}"
    # gpu_clean.lock msvcrt dosya kilidi: dosyanin VARLIGI kilitli demek degil (OS surec olunce birakir) -> kilidi sinamiyoruz.
    if used > 1500 and not cl:
        add("GPU kilit/kullanim", WARN, d + "; temizlik sureci yok ama GPU dolu (SigLIP/chatterbox/Sopro olabilir)",
            "Gece GPU temizligi oncesi nvidia-smi ile sahibini bul")
    else:
        add("GPU kilit/kullanim", OK, d)
    # mkdir tipi kilitler (runner-kill-orphans-1106): dizin kilit + pid dosyasi, olu pid
    stale = []
    for root in (Path(r"C:\Users\meteh\testbench"), Path(r"C:\Users\meteh\CodexOutputs")):
        try:
            for dp in root.glob("*/out/*.lock"):
                if dp.is_dir():
                    pf = next((x for x in dp.iterdir() if x.suffix in (".pid", "") or x.name == "pid"), None)
                    if pf:
                        try:
                            pid = int(pf.read_text().strip().split()[0])
                            if not psutil.pid_exists(pid):
                                stale.append(f"{dp} (pid {pid} olu)")
                        except Exception:
                            pass
        except Exception:
            pass
    add("Olu pid'li mkdir kilitleri", WARN if stale else OK, "; ".join(stale[:3]) if stale else "yok (testbench/*/out/*.lock)",
        "Runner 'waiting' takiliyorsa kilidi kaldir" if stale else "")


def chk_misc():
    up = (time.time() - psutil.boot_time()) / 86400
    add("Calisma suresi", WARN if up > 5 else OK, f"{up:.1f} gun yeniden baslatmasiz",
        "Pagefile/arena birikimi icin hafta basinda yeniden baslat" if up > 5 else "")
    big = []
    for p in (r"C:\hiberfil.sys", r"C:\pagefile.sys"):
        try:
            big.append(f"{Path(p).name} {Path(p).stat().st_size / GB:.1f} GB")
        except Exception:
            pass
    add("Sistem dosyalari", INFO, ", ".join(big))
    # docker/wsl bos mu (SearXNG preflight'ta ayri)
    try:
        wsl = [p for p in psutil.process_iter(["name"]) if p.info["name"].lower() in ("vmmem", "vmmemwsl")]
        add("Docker/WSL vmmem", INFO, f"{len(wsl)} surec" + (f", {sum(p.memory_info().rss for p in wsl) / GB:.1f} GB" if wsl else ""))
    except Exception:
        pass


def main():
    t0 = time.time()
    for fn in (chk_commit, chk_disk):
        try:
            fn()
        except Exception as e:
            add(fn.__name__, WARN, f"kontrol coktu: {type(e).__name__}: {e}")
    ports = {}
    try:
        ports = chk_processes()
    except Exception as e:
        add("chk_processes", WARN, f"kontrol coktu: {type(e).__name__}: {e}")
    for fn, a in ((chk_gpu, (ports,)), (chk_misc, ())):
        try:
            fn(*a)
        except Exception as e:
            add(fn.__name__, WARN, f"kontrol coktu: {type(e).__name__}: {e}")
    t = time.time() - t0
    if "--json" in sys.argv:
        print(json.dumps({"sure_sn": round(t, 1), "sonuclar": R}, ensure_ascii=False, indent=2))
    else:
        w = max(len(r["ad"]) for r in R)
        for r in R:
            print(f"[{r['durum']:<5}] {r['ad']:<{w}}  {r['detay']}")
            if r["yapilacak"] and r["durum"] in (FAIL, WARN):
                print(f"        -> {r['yapilacak']}")
        print(f"\nSure: {t:.1f} sn")
    sys.exit(1 if any(r["durum"] == FAIL for r in R) else 0)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
