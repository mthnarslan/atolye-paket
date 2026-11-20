#!/usr/bin/env python
"""Render HyperFrames chunks (scenefile work/<film>/hf_NN) on a remote host and fetch out.mp4 back.

  python remote_render.py <film work dir> hf_06 hf_07 ... --host a1|vds [--par N] [--w N]
  python remote_render.py <film work dir> --all --host a1          # every hf_NN without out.mp4

Per chunk: pack (chunk dir + only the assets its html references + assets/fonts) -> scp -> remote render
-> scp out.mp4 back -> ffprobe duration check against chunk.json (b-a) -> rename to <chunk>/out.mp4.
Resumable: a chunk whose local out.mp4 already has the right duration is skipped. Remote job dir is removed
after a verified download (kept on failure so a re-run can look at it).
Never touches the local renderer, sf.py, or chrome.
"""
import argparse, json, os, re, subprocess, sys, tarfile, tempfile, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FPS = 25
HOSTS = {
    # ssh target, remote job root, shell prelude, render prefix, default parallel renders, workers per render
    "a1": dict(ssh="a1", root="~/hf/jobs",
               pre="export HYPERFRAMES_BROWSER_PATH=$HOME/.cache/ms-playwright/chromium_headless_shell-1254/"
                   "chrome-headless-shell-linux-arm64/chrome-headless-shell PRODUCER_FORCE_SCREENSHOT=true; cd ~/hf",
               nice="nice -n 5", par=3, w=1),
    "vds": dict(ssh="root@<IP-gizli>", root="/root/offload_test/jobs",
                pre="export PATH=/root/offload_test/node-v22.12.0-linux-x64/bin:$PATH; cd /root/offload_test/hfcli",
                nice="nice -n 19", par=1, w=3),
}
ASSET_RE = re.compile(r"""assets/[^"'()\s<>\\;,]+""")
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "-o", "ServerAliveInterval=30"]
_print = threading.Lock()


def log(*a):
    with _print:
        print(time.strftime("%H:%M:%S"), *a, flush=True)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def expect_dur(chunk_dir):
    c = json.loads((chunk_dir / "chunk.json").read_text(encoding="utf8"))
    return float(c["b"]) - float(c["a"])


def out_ok(chunk_dir):
    out = chunk_dir / "out.mp4"
    if not out.is_file() or out.stat().st_size < 1e5:
        return False
    d = duration(out)
    return d is not None and abs(d - expect_dur(chunk_dir)) <= 0.12


def referenced_assets(chunk_dir, assets_root):
    files = [chunk_dir / "index.html"] + sorted((chunk_dir / "compositions").glob("*.html")) if (chunk_dir / "compositions").is_dir() else [chunk_dir / "index.html"]
    refs = set()
    for f in files:
        if f.is_file():
            for m in ASSET_RE.findall(f.read_text(encoding="utf8", errors="ignore")):
                refs.add(m.split("?")[0].split("#")[0].replace("%20", " "))
    keep, missing = [], []
    for r in sorted(refs):
        p = assets_root / r[len("assets/"):]
        (keep if p.is_file() else missing).append((r, p))
    return keep, missing


def pack(chunk_dir, assets_root, tgz):
    keep, missing = referenced_assets(chunk_dir, assets_root)
    skip = {"out.mp4", "render.log", "renders"}
    with tarfile.open(tgz, "w:gz", compresslevel=1) as t:
        for p in chunk_dir.iterdir():
            if p.name in skip or p.name == "assets":
                continue
            t.add(p, arcname=p.name)
        for r, p in keep:
            t.add(p, arcname=r)
        fonts = assets_root / "fonts"
        if fonts.is_dir():
            for p in fonts.rglob("*"):
                if p.is_file() and f"assets/fonts/{p.relative_to(fonts).as_posix()}" not in {k for k, _ in keep}:
                    t.add(p, arcname="assets/fonts/" + p.relative_to(fonts).as_posix())
    return len(keep), missing


def ssh(host, cmd, timeout=None):
    return run(["ssh", *SSH_OPTS, host["ssh"], cmd], timeout=timeout)


def scp(src, dst, tries=3):
    for i in range(tries):
        r = run(["scp", "-q", *SSH_OPTS, src, dst])
        if r.returncode == 0:
            return True
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"scp {src} -> {dst} failed: {r.stderr.strip()[:200]}")


def do_chunk(film_dir, name, host, w):
    chunk = film_dir / name
    if out_ok(chunk):
        log(f"{name}: local out.mp4 ok, skip")
        return name, "skip", 0
    t0 = time.time()
    film = film_dir.name
    rdir = f"{host['root']}/{film}/{name}"
    with tempfile.TemporaryDirectory() as td:
        tgz = Path(td) / f"{name}.tgz"
        n, missing = pack(chunk, film_dir / "assets", tgz)
        mb = tgz.stat().st_size / 1e6
        if missing:
            log(f"{name}: WARNING {len(missing)} referenced assets missing locally, e.g. {missing[0][0]}")
        t1 = time.time()
        r = ssh(host, f"rm -rf {rdir}; mkdir -p {rdir}")
        if r.returncode:
            raise RuntimeError(f"{name}: ssh mkdir failed: {r.stderr.strip()[:200]}")
        scp(str(tgz), f"{host['ssh']}:{rdir}/in.tgz")
        t2 = time.time()
        log(f"{name}: packed {n} assets, {mb:.1f} MB, upload {t2 - t1:.0f}s ({mb / max(t2 - t1, .1):.1f} MB/s)")
    r = ssh(host, f"cd {rdir} && tar xzf in.tgz && rm in.tgz")
    if r.returncode:
        raise RuntimeError(f"{name}: untar failed: {r.stderr.strip()[:200]}")
    cmd = (f"{host['pre']}; /usr/bin/time -f 'peakKB=%M cpu=%U+%S wall=%e' {host['nice']} "
           f"npx hyperframes render {rdir} -o {rdir}/out.mp4 -f {FPS} --crf 18 -w {w} --quiet")
    t3 = time.time()
    r = ssh(host, f"bash -c {sh_quote(cmd)} > {rdir}/render.log 2>&1; echo rc=$?; tail -n 1 {rdir}/render.log")
    tail = r.stdout.strip().replace("\n", " | ")
    if "rc=0" not in r.stdout:
        raise RuntimeError(f"{name}: remote render failed ({tail[:300]}); see {rdir}/render.log on host")
    t4 = time.time()
    log(f"{name}: rendered in {t4 - t3:.0f}s ({expect_dur(chunk) / (t4 - t3):.2f} video-s/s) {tail[-70:]}")
    part = chunk / "out.mp4.part"
    scp(f"{host['ssh']}:{rdir}/out.mp4", str(part))
    d = duration(part)
    exp = expect_dur(chunk)
    if d is None or abs(d - exp) > 0.12:
        raise RuntimeError(f"{name}: duration {d} != expected {exp:.2f}; kept {part}")
    os.replace(part, chunk / "out.mp4")
    ssh(host, f"rm -rf {rdir}")
    log(f"{name}: done in {time.time() - t0:.0f}s total (dur {d:.2f}s)")
    return name, "ok", time.time() - t0


def sh_quote(s):
    return "'" + s.replace("'", "'\\''") + "'"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film_dir")
    ap.add_argument("chunks", nargs="*")
    ap.add_argument("--host", default="a1", choices=list(HOSTS))
    ap.add_argument("--par", type=int, help="chunks rendered at once on the host")
    ap.add_argument("--w", type=int, help="hyperframes -w per render")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    film_dir = Path(a.film_dir).resolve()
    host = HOSTS[a.host]
    names = a.chunks or []
    if a.all:
        names = sorted(p.name for p in film_dir.glob("hf_[0-9][0-9]"))
    par, w = a.par or host["par"], a.w or host["w"]
    log(f"{film_dir.name}: {len(names)} chunks -> {a.host}, {par} at once, -w {w}")
    fails = []
    with ThreadPoolExecutor(par) as ex:
        futs = {ex.submit(do_chunk, film_dir, n, host, w): n for n in names}
        for f, n in futs.items():
            try:
                f.result()
            except Exception as e:
                log(f"{n}: FAILED {e}")
                fails.append(n)
    log("done; failed: " + (", ".join(fails) or "none"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
