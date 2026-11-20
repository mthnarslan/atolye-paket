"""Full end-to-end test: every film runs its own async chain, all films at once.

python fullrun.py <parent folder> [tag]

Per film:  drive.py 1 (one film at a time: Chatterbox is serial) -> drive.py 2-3
           -> drive.py 4 (old render + QA) next to sf.py plan, prep, build; QA still gates the package
           -> sf.py render (one film at a time: it already spreads chunks over local + a1 + vds)
           -> sf.py mix (one at a time: NVENC, keeps the 2-ffmpeg cap)
           -> v3_package.py (ZIP)
drive.py exit codes are handled like queue_films.py, with shorter waits (nobody idles 10 min).
Every step writes a start/end line to Belgesel_Teslim/fullrun_<tag>/timeline.jsonl; summary.md at the end.
"""
import ctypes, json, os, re, subprocess, sys, threading, time
from pathlib import Path

ATTACH = "--attach" in sys.argv     # pick up the drive.py processes an earlier fullrun of the same tag left running
_args = [a for a in sys.argv[1:] if a != "--attach"]
PARENT = Path(_args[0])
TAG = _args[1] if len(_args) > 1 else time.strftime("%m%d_%H%M")
ENG = Path(r"C:\Users\meteh\Kanallar\Engineered")
DRIVE, SF, PKG = ENG / "tools/drive.py", ENG / "scenefile/sf.py", ENG / "tools/v3_package.py"
CODEX = Path(r"C:\Users\meteh\CodexOutputs")
VOICEFIX = Path(r"C:\Users\meteh\testbench\speed_1106\voicefix.py")
OUT = Path(r"C:\Users\meteh\Belgesel_Teslim") / f"fullrun_{TAG}"
OUT.mkdir(parents=True, exist_ok=True)
TL = OUT / "timeline.jsonl"
class Slot:
    """Cross-process slot: every fullrun on this PC (several chat sessions at once) shares the same voice,
    render and mix slots through lock files, so two sessions never voice or render on top of each other."""
    DIR = Path(r"C:\Users\meteh\Belgesel_Teslim\_slots")

    def __init__(self, name, n=1):
        self.paths = [self.DIR / f"{name}{i}.lock" for i in range(n)]
        self.DIR.mkdir(parents=True, exist_ok=True)
        self.local = threading.local()

    def __enter__(self):
        import msvcrt
        while True:
            for p in self.paths:
                f = open(p, "a+b")
                try:
                    f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    self.local.f = f
                    return self
                except OSError:
                    f.close()
            time.sleep(3)

    def try_enter(self):
        import msvcrt
        for p in self.paths:
            f = open(p, "a+b")
            try:
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                self.local.f = f
                return True
            except OSError:
                f.close()
        return False

    def __exit__(self, *a):
        import msvcrt
        f = self.local.f
        try:
            f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            f.close()


RENDER, MIX, VOICE = Slot("render"), Slot("mix"), Slot("voice")
# Second render lane: while one film holds this PC's render slot, the next film renders on a1+vds only
# (sf render --remote-only). The local render keeps the servers too only when no other film of this run
# still waits to render. Off: FULLRUN_REMOTE_LANE=0.
REMOTE_LANE = Slot("render_remote")
REMOTE_ON = os.environ.get("FULLRUN_REMOTE_LANE", "1") != "0"
UNRENDERED = set()                 # a film with the local slot keeps the servers unless another film is waiting
_UL = threading.Lock()
WAIT = {10: 120, 11: 120, 13: 120, 3: 180, 4: 180}   # 11 = bridge still runs this folder's job
ENV = {**__import__("os").environ, "PYTHONIOENCODING": "utf-8"}
lock = threading.Lock()


def free_gb():
    class M(ctypes.Structure):
        _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in
                    ("total", "avail", "pt", "pa", "vt", "va", "ve")]
    m = M(); m.l = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.avail / 2**30


def ev(film, step, **kw):
    rec = dict(t=time.strftime("%H:%M:%S"), ts=round(time.time(), 1), film=film, step=step, **kw)
    with lock, open(TL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec), flush=True)


def run(film, step, args, logname, stop=None):
    """stop: polled every 5 s; once it returns True the step is killed and "stopped" is returned."""
    while free_gb() < 2.0:
        time.sleep(15)
    t = time.time(); ev(film, step, phase="start", ram=round(free_gb(), 1))
    with open(OUT / logname, "a", encoding="utf-8") as lf:
        lf.write(f"\n===== {step} {time.strftime('%H:%M:%S')}\n"); lf.flush()
        p = subprocess.Popen([sys.executable, *map(str, args)], stdout=lf, stderr=subprocess.STDOUT, env=ENV)
        while True:
            try:
                code = p.wait(timeout=5); break
            except subprocess.TimeoutExpired:
                if stop and stop():
                    kill_tree(p.pid); p.wait(); code = "stopped"; break
    ev(film, step, phase="end", code=code, sec=round(time.time() - t))
    return code


def handover(film):
    """True (holding the local render slot) when the local slot is free and the servers still have >=30% of the film."""
    work = (Path(os.environ["SF_WORK_DIR"]) if os.environ.get("SF_WORK_DIR") else SF.parent / "work") / film
    dirs = list(work.glob("hf_[0-9][0-9]"))
    left = sum(not (d / "out.mp4").exists() for d in dirs)
    if not dirs or left < 0.3 * len(dirs) or not RENDER.try_enter():
        return False
    return True


def stop_remote(film):
    """Best effort: stop this film's orphaned server renders (the killed ssh client does not stop them)."""
    for host in ("a1", "root@<IP-gizli>"):
        try:
            subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host,
                            f"pkill -f '[j]obs/{film}/' ; true"], capture_output=True, timeout=30)
        except Exception:
            pass


def kill_tree(pid):
    """Kill a step and its children (sf render's ffmpeg/ssh); remote jobs finish on their own, their chunks are reused."""
    import psutil
    try:
        root = psutil.Process(pid)
        for c in root.children(recursive=True) + [root]:
            try:
                c.kill()
            except psutil.Error:
                pass
    except psutil.Error:
        pass


def synth_done(film, since):
    """True once this run of stage 1 has written master_voiceover.wav (synthesis over; ASR + audit follow)."""
    wav = Path(r"C:\Users\meteh\CodexOutputs") / film / "master_voiceover.wav"
    try:
        return wav.stat().st_mtime >= since - 1 and wav.stat().st_size > 1e6
    except OSError:
        return False


def run_release(film, step, args, logname, slot, ready):
    """run() holding `slot` (already entered); the slot is released as soon as ready() is true, else at the end."""
    done, rel = threading.Event(), threading.Lock()
    state = {"f": slot.local.f}            # the lock handle belongs to this thread; the watcher unlocks it directly

    def release(why):
        import msvcrt
        with rel:
            f, state["f"] = state["f"], None
            if f is None:
                return
            try:
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            finally:
                f.close()
            if why: ev(film, "voice slot released early", sec=round(time.time() - t0))

    def watch():
        while not done.wait(2):
            if ready():
                release("early"); return
    t0 = time.time()
    threading.Thread(target=watch, daemon=True).start()
    try:
        return run(film, step, args, logname)
    finally:
        done.set(); release(None)


def failed_stage(log, default):
    found = re.findall(r"^REASON \S+ stage (\d):", log.read_text(encoding="utf-8", errors="replace"), re.M)
    return int(found[-1]) if found else default


def drive_loop(film, folder, start, end, log):
    """drive.py from `start` to `end` with queue_films-style retries. Stage 1 runs alone, under VOICE."""
    tries = {}
    while True:
        if start == 1:
            # Chatterbox serves one request at a time (LOCK in chatterbox_serve.py): four films
            # voicing together all finish at the end. One at a time, the first film reaches
            # plan/materials (GPT, Flash, downloads) ~3/4 of the voice time earlier.
            tw = time.time()
            VOICE.__enter__()
            if time.time() - tw > 5:
                ev(film, "waited for voice slot", sec=round(time.time() - tw))
            # Pocket synthesis (~200-520 s) is the only serial part of stage 1; the ASR (VDS/a1) and the
            # Gemini audit (~300+300 s, EP02/EP03 1106 file times) run outside the slot, so the next film's
            # synthesis starts as soon as this film's master_voiceover.wav is written.
            code = run_release(film, "drive 1-1", [DRIVE, folder, 1, 1], log.name, VOICE, lambda: synth_done(film, tw))
            if code == 0:
                if end == 1:
                    return True
                start = 2
                continue
            # Audit FAIL on off-voice or dropped words that the engine's 3 repair rounds did not reach
            # (EP02 sifir_1107: rounds spent on one drifting chunk, two dropped phrases left): re-seed just
            # those chunks with voicefix and rerun stage 1 (other chunks come from the chunk cache). Twice at most.
            if code == 1 and tries.get("voicefix", 0) < 2:
                tries["voicefix"] = tries.get("voicefix", 0) + 1
                fx = subprocess.run([sys.executable, str(VOICEFIX), str(CODEX / film), "--apply"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
                if "applied" in fx.stdout:
                    ev(film, "voicefix", n=tries["voicefix"], chunks=fx.stdout.count("seed "))
                    continue
        else:
            code = run(film, f"drive {start}-{end}", [DRIVE, folder, start, end], log.name)
        if code == 0:
            return True
        if code in WAIT and tries.get(code, 0) < 3:
            tries[code] = tries.get(code, 0) + 1
            start = failed_stage(log, start) if code in (10, 11) else 1 if code == 13 else 3
            ev(film, "retry", code=code, next=start, n=tries[code], wait=WAIT[code])
            time.sleep(WAIT[code])
            continue
        ev(film, "FAILED", where=f"drive {start}-{end}", code=code)
        return False


def shot_stamp(film):
    shots = Path(r"C:\Users\meteh\CodexOutputs") / film / "03_materials" / "shots"
    return {p.parent.name: p.stat().st_mtime for p in shots.glob("*/result.json")}


def attached_tail(log):
    """Text of the log after the last drive header (the drive.py left running by an earlier fullrun)."""
    t = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    return t[t.rfind("===== drive"):] if "===== drive" in t else ""


def attach_wait(film, folder, log, upto):
    """--attach: follow a drive.py an earlier fullrun started (still writing to the log) until stage `upto`
    passed (3) or the whole drive ended (4). A failed drive falls back to drive_loop from its failed stage."""
    ok3 = re.compile(r"^\[stage 3\] http=200 status=MATERIALS_READY", re.M)
    while True:
        t = attached_tail(log)
        if "ALL STAGES DONE" in t or (upto == 3 and ok3.search(t)):
            return True
        m = re.findall(r"^REASON \S+ stage (\d):", t, re.M)
        if m:
            st = int(m[-1])
            ev(film, "attached drive failed", stage=st)
            return drive_loop(film, folder, 3 if st == 4 else st, upto, log)
        time.sleep(10)


def render_step(film, log):
    """Local render slot first; if another film holds it, render on the servers alone. A failed remote render
    falls back to the local slot (chunks the servers finished are reused)."""
    tw, remote_ok = time.time(), REMOTE_ON
    with _UL:
        UNRENDERED.add(film)               # films of this run waiting for / in render
    try:
        while True:
            if RENDER.try_enter():
                try:
                    if time.time() - tw > 5:
                        ev(film, "waited for render slot", sec=round(time.time() - tw))
                    with _UL:
                        others = bool(UNRENDERED - {film})
                    servers = REMOTE_ON and not others and REMOTE_LANE.try_enter()
                    try:
                        return run(film, "sf render", [SF, film, "render"] + ([] if servers or not REMOTE_ON else ["--local-only"]), log.name)
                    finally:
                        if servers:
                            REMOTE_LANE.__exit__()
                finally:
                    RENDER.__exit__()
            if remote_ok and REMOTE_LANE.try_enter():
                try:
                    ev(film, "render on servers", waited=round(time.time() - tw))
                    rc = run(film, "sf render remote", [SF, film, "render", "--remote-only"], log.name,
                             stop=lambda: handover(film))
                finally:
                    REMOTE_LANE.__exit__()
                if rc == 0:
                    return 0
                if rc == "stopped":                 # local slot freed: we hold it now; finish here (server chunks done so far are reused)
                    try:
                        ev(film, "render moved to local slot")
                        stop_remote(film)
                        return run(film, "sf render", [SF, film, "render", "--local-only"], log.name)
                    finally:
                        RENDER.__exit__()
                remote_ok = False
                ev(film, "remote render failed, waiting for local slot")
            time.sleep(5)
    finally:
        with _UL:
            UNRENDERED.discard(film)


def film_chain(folder):
    film, t0 = folder.name, time.time()
    log = OUT / f"{film}.log"
    if ATTACH:
        if not attach_wait(film, folder, log, 3):
            ev(film, "FAILED", where="drive 1-3", total=round(time.time() - t0)); return
        ev(film, "stage 3 done (attached)")
        stage4 = lambda: attach_wait(film, folder, log, 4)
    else:
        if not drive_loop(film, folder, 1, 3, log):
            ev(film, "FAILED", where="drive 1-3", total=round(time.time() - t0)); return
        stage4 = lambda: drive_loop(film, folder, 4, 4, log)
    # Stage 4 (old-style render + delivery QA) is not an input of the V3 build, so it runs next to
    # sf plan/prep/build instead of before them. Its QA still gates the package; if stage 4 had to
    # remake shots, the V3 steps run again on the new shots.
    stamp, s4 = shot_stamp(film), {}
    t4 = threading.Thread(target=lambda: s4.setdefault("ok", stage4()))
    t4.start()
    sf_ok = all(run(film, f"sf {st}", [SF, film, st], log.name) == 0 for st in ("plan", "prep", "build"))
    t4.join()
    if not s4.get("ok"):
        ev(film, "FAILED", where="stage 4 QA", total=round(time.time() - t0)); return
    if not sf_ok or shot_stamp(film) != stamp:
        ev(film, "redo sf", why="sf failed" if not sf_ok else "stage 4 changed shots")
        for st in ("plan", "prep", "build"):
            if run(film, f"sf {st}", [SF, film, st], log.name):
                ev(film, "FAILED", where=f"sf {st}", total=round(time.time() - t0)); return
    if render_step(film, log):
        ev(film, "FAILED", where="sf render", total=round(time.time() - t0)); return
    tw = time.time()
    with MIX:
        if time.time() - tw > 5:
            ev(film, "waited for mix slot", sec=round(time.time() - tw))
        if run(film, "sf mix", [SF, film, "mix"], log.name):
            ev(film, "FAILED", where="sf mix", total=round(time.time() - t0)); return
    run(film, "package", [PKG, film], log.name)
    ev(film, "DONE", total=round(time.time() - t0))


films = sorted(p for p in PARENT.iterdir() if p.is_dir())
ev("ALL", "start", films=[f.name for f in films])
T0 = time.time()
th = []
for f in films:
    t = threading.Thread(target=lambda f=f: (film_chain(f), UNRENDERED.discard(f.name))); t.start(); th.append(t)
    time.sleep(0 if ATTACH else 20)      # stagger the bridge submissions a little
for t in th:
    t.join()
total = round(time.time() - T0)
ev("ALL", "end", total=total)

rows = [json.loads(l) for l in TL.read_text(encoding="utf-8").splitlines()]
md = [f"# fullrun {TAG}: {len(films)} films, wall {total} s ({total/60:.0f} min)\n", "| film | step | sec | code |", "|---|---|---|---|"]
md += [f"| {r['film']} | {r['step']} | {r.get('sec', r.get('total', ''))} | {r.get('code', '')} |" for r in rows if r.get("phase") == "end" or r["step"] in ("DONE", "FAILED", "retry")]
(OUT / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
