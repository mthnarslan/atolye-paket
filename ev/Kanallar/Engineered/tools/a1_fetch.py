"""Download YouTube sources on the Oracle box (ssh a1) through its socks proxies, pull them to the PC.

  python a1_fetch.py OUTDIR URL_OR_ID... | -l urls.txt | -j catalog.json|source_selection.json [-n 8] [--keep-remote]

Whole files (video-only 1080p avc1 mp4, the pipeline's ladder) are fetched: --download-sections cannot
go through socks. One proxy per job, a failed job retries on another proxy. Each finished file is scp'd
back while the others still download. Files already in OUTDIR are skipped. Proxy URLs stay on a1.
Prints per-file and total MB/s. Max 8 concurrent (proxies are shared with 9router).
"""
import argparse, json, re, subprocess, sys, threading, time, os
from pathlib import Path

HOST = "a1"
FMT = ("bestvideo[height<=1080][ext=mp4][vcodec^=avc1][format_id!*=hls]/"
       "bestvideo[height<=1080][ext=mp4][format_id!*=hls]/best[height<=1080][ext=mp4]")
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=20"]

WORKER = r'''
import sys, json, subprocess, threading, queue, time, os, glob
ids, n, fmt, rdir, tries = json.loads(sys.stdin.read())
os.makedirs(rdir, exist_ok=True)
proxies = [l.strip() for l in open(os.path.expanduser("~/proxies.txt")) if l.strip()]
free = queue.Queue()
for i in range(len(proxies)): free.put(i)
bad = {}
lock = threading.Lock()
def say(**k):
    with lock: print(json.dumps(k), flush=True)
def job(vid):
    err = ""
    for a in range(tries):
        i = free.get()
        t = time.time()
        try:
            for f in glob.glob(f"{rdir}/{vid}.*"): os.remove(f)
            r = subprocess.run(["yt-dlp", "--js-runtimes", "node", "--proxy", proxies[i], "-f", fmt, "--no-playlist", "-q",
                "--no-warnings", "--socket-timeout", "30", "--retries", "3", "-o", f"{rdir}/{vid}.%(ext)s",
                "https://www.youtube.com/watch?v=" + vid], capture_output=True, text=True, timeout=1800)
            fs = [f for f in glob.glob(f"{rdir}/{vid}.*") if not f.endswith((".part", ".ytdl"))]
            if r.returncode == 0 and fs:
                sz = os.path.getsize(fs[0])
                say(ev="done", id=vid, file=os.path.basename(fs[0]), size=sz, secs=round(time.time() - t, 1), proxy=i + 1, attempt=a + 1)
                free.put(i); return
            err = (r.stderr or "").strip().splitlines()[-1][:160] if r.stderr else f"rc={r.returncode}"
        except Exception as e:
            err = type(e).__name__
        say(ev="retry", id=vid, proxy=i + 1, err=err)
        free.put(i)
    say(ev="fail", id=vid, err=err)
q = queue.Queue()
for v in ids: q.put(v)
def w():
    while True:
        try: v = q.get_nowait()
        except queue.Empty: return
        job(v)
ts = [threading.Thread(target=w) for _ in range(min(n, len(proxies), len(ids)))]
[t.start() for t in ts]; [t.join() for t in ts]
say(ev="end")
'''


def vid_of(s):
    m = re.search(r"(?:v=|youtu\.be/|^)([\w-]{11})(?:[&?/]|$)", s.strip())
    return m.group(1) if m else None


def gather(args):
    out = list(args.items)
    if args.list:
        out += Path(args.list).read_text(encoding="utf8").split()
    if args.json:
        s = Path(args.json).read_text(encoding="utf8")
        out += re.findall(r"https://www\.youtube\.com/watch\?v=[\w-]{11}", s)
    ids = []
    for s in out:
        v = vid_of(s)
        if v and v not in ids:
            ids.append(v)
    return ids


def pull(rdir, name, dest, tmp_suffix=".a1part"):
    t = time.time()
    tmp = dest / (name + tmp_suffix)
    r = subprocess.run(["scp", "-q", f"{HOST}:{rdir}/{name}", str(tmp)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:200])
    tmp.replace(dest / name)
    return time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("items", nargs="*")
    ap.add_argument("-l", "--list")
    ap.add_argument("-j", "--json")
    ap.add_argument("-n", type=int, default=8)
    ap.add_argument("--pull-parallel", type=int, default=3)
    ap.add_argument("--tries", type=int, default=3)
    ap.add_argument("--keep-remote", action="store_true")
    args = ap.parse_args()
    dest = Path(args.outdir)
    dest.mkdir(parents=True, exist_ok=True)
    ids = gather(args)
    have = {p.stem for p in dest.glob("*.mp4") if p.stat().st_size > 0}
    todo = [v for v in ids if v not in have]
    print(f"{len(ids)} urls, {len(ids) - len(todo)} already present, {len(todo)} to fetch")
    if not todo:
        return 0
    n = min(max(1, args.n), 8)
    rdir = f"/home/ubuntu/fetch/{int(time.time())}"
    t0 = time.time()
    wk = dest / ".a1_worker.py"
    wk.write_text(WORKER.replace("sys.stdin.read()", "sys.stdin.readline()"), encoding="utf8")
    subprocess.run(["scp", "-q", str(wk), f"{HOST}:/tmp/a1_worker.py"], check=True)
    wk.unlink()
    p = subprocess.Popen(SSH + [HOST, "python3 -u /tmp/a1_worker.py"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    p.stdin.write(json.dumps([todo, n, FMT, rdir, args.tries]) + chr(10))
    p.stdin.close()
    sem = threading.Semaphore(args.pull_parallel)
    rows, threads, fails = {}, [], []

    def puller(ev):
        with sem:
            try:
                secs = pull(rdir, ev["file"], dest)
                rows[ev["id"]] = (ev["size"], ev["secs"], secs)
                mb = ev["size"] / 1e6
                print(f"  {ev['id']} {mb:7.1f} MB  a1 dl {ev['secs']:6.1f}s ({mb / max(ev['secs'], .1):4.1f} MB/s, proxy{ev['proxy']})  pull {secs:5.1f}s ({mb / max(secs, .1):4.1f} MB/s)", flush=True)
            except Exception as e:
                fails.append(ev["id"])
                print(f"  {ev['id']} PULL FAIL {e}", flush=True)

    for line in p.stdout:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev["ev"] == "done":
            t = threading.Thread(target=puller, args=(ev,))
            t.start(); threads.append(t)
        elif ev["ev"] == "retry":
            print(f"  {ev['id']} retry (proxy{ev['proxy']}): {ev['err']}", flush=True)
        elif ev["ev"] == "fail":
            fails.append(ev["id"])
            print(f"  {ev['id']} FAIL: {ev['err']}", flush=True)
    p.wait()
    for t in threads:
        t.join()
    wall = time.time() - t0
    tot = sum(r[0] for r in rows.values()) / 1e6
    print(f"TOTAL {len(rows)}/{len(todo)} files, {tot:.0f} MB, wall {wall:.0f}s = {tot / max(wall, .1):.2f} MB/s end-to-end; failed {len(fails)}")
    if not args.keep_remote:
        subprocess.run(SSH + [HOST, f"rm -rf {rdir}"], capture_output=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
