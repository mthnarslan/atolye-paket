"""Run every episode folder under a parent through drive.py, a few at a time.

python queue_films.py "<parent folder>" [max_parallel=3]

A film starts only while fewer than max_parallel run (or wait for a retry) and
free RAM is above 1.5 GB when nothing else runs, 2.5 GB when something does.
drive.py exit codes decide what happens next:
  0   done
  3/4 stopped in stage 3 or 4: resume from stage 3 after 10 min, at most 3 times
  10  transport error (REASON line names the stage): retry that stage after 5 min, at most 3 times
  11  the bridge already runs this folder: never relaunched
  12  stage-1 audit-only rerun timed out: FAILED
  13  stage-1 audit unverified only by Gemini transport errors: stage 1 again after 5 min, at most 3 times
  other (1, 2, ...) FAILED
Progress goes to Belgesel_Teslim/batch.log, which supervisor.py also reads.
"""
import ctypes
import re
import subprocess
import sys
import time
from pathlib import Path

PARENT = Path(sys.argv[1])
MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 3
DRIVE = Path(__file__).with_name("drive.py")
OUT = Path(r"C:\Users\meteh\Belgesel_Teslim")
LOGS = OUT / "queue"
LOGS.mkdir(parents=True, exist_ok=True)


def free_gb():
    class M(ctypes.Structure):
        _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in
                    ("total", "avail", "pt", "pa", "vt", "va", "ve")]
    m = M(); m.l = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.avail / 2**30


def log(msg):
    with open(OUT / "batch.log", "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def launch(folder, start):
    out = open(LOGS / (folder.name + ".log"), "a", encoding="utf-8")
    return subprocess.Popen([sys.executable, str(DRIVE), str(folder), str(start), "4"], stdout=out, stderr=out,
                            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})


RETRY_WAIT = {10: 300, 13: 300, 3: 600, 4: 600}  # seconds before the next attempt


def failed_stage(folder, default):
    """Stage named by the last 'REASON ... stage N:' line of the film's queue log."""
    try:
        text = (LOGS / (folder.name + ".log")).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return default
    found = re.findall(r"^REASON \S+ stage (\d):", text, re.M)
    return int(found[-1]) if found else default


todo = sorted(p for p in PARENT.iterdir() if p.is_dir())
running, retries, waiting, starts = {}, {}, {}, {}
log(f"queue start: {len(todo)} films, max {MAX}")
while todo or running or waiting:
    for folder, proc in list(running.items()):
        code = proc.poll()
        if code is None:
            continue
        del running[folder]
        if code == 0:
            log(f"{folder.name} DONE")
        elif code == 11:
            log(f"{folder.name} duplicate job in the bridge (exit 11), not relaunched")
        elif code in RETRY_WAIT and retries.get((folder, code), 0) < 3:
            retries[folder, code] = retries.get((folder, code), 0) + 1
            nxt = failed_stage(folder, starts[folder]) if code == 10 else 1 if code == 13 else 3
            waiting[folder] = (time.time() + RETRY_WAIT[code], nxt)
            log(f"{folder.name} exit {code}, resume from stage {nxt} in {RETRY_WAIT[code] // 60} min "
                f"(retry {retries[folder, code]}/3)")
        elif code == 12:
            log(f"{folder.name} FAILED: stage-1 audit rerun timed out (exit 12)")
        else:
            log(f"{folder.name} FAILED at stage {code}")
    for folder, (ready, nxt) in list(waiting.items()):
        if time.time() >= ready and len(running) < MAX:
            del waiting[folder]
            starts[folder] = nxt
            running[folder] = launch(folder, nxt)
    if todo and len(running) + len(waiting) < MAX and free_gb() > (1.5 if not running else 2.5):
        folder = todo.pop(0)
        log(f"{folder.name} start (free RAM {free_gb():.1f} GB)")
        starts[folder] = 1
        running[folder] = launch(folder, 1)
        time.sleep(90)  # let its stage 1-2 settle before judging RAM again
    time.sleep(20)
log("queue finished")
