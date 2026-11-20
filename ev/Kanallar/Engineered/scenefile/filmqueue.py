"""Queue for EP03, EP05, EP02 after EP04: re-plan with current code (GPT answers cached), prep+build at once, render one film at a time
(after EP04's render), mix in the background while the next film renders. Log: queue.log"""
import subprocess, sys, time, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILMS = ["EP05_Tornado_Ratings_Explained", "EP02_Enderlin_ND_2025"]
env = dict(os.environ, PYTHONIOENCODING="utf-8")


def log(m):
    print(time.strftime("%H:%M:%S"), m, flush=True)


def run(film, step, *extra):
    t = time.time(); log(f"{film} {step} ...")
    with open(HERE / f"q_{film}_{step}.log", "w", encoding="utf8") as f:
        r = subprocess.run([sys.executable, "sf.py", film, step, *extra], cwd=HERE, stdout=f, stderr=subprocess.STDOUT, env=env)
    log(f"{film} {step} exit {r.returncode} in {time.time()-t:.0f}s")
    if r.returncode:
        raise SystemExit(f"{film} {step} failed, see q_{film}_{step}.log")


def old_plan_done(film):
    f = HERE / f"plan_{film}.log"
    return not f.exists() or "plan done" in f.read_text(encoding="utf8", errors="replace") or "Traceback" in f.read_text(encoding="utf8", errors="replace")


mixes = []
for film in FILMS:
    while not old_plan_done(film):
        time.sleep(20)
    if film != "EP03_Nepal_Tibet_Glacier_Flood_2026":      # EP03 already re-planned with the current code
        run(film, "plan")
    run(film, "prep"); run(film, "build")
    while "render done" not in (HERE / "run_EP04.log").read_text(encoding="utf8", errors="replace"):
        time.sleep(20)
    run(film, "render", "--par", "2")
    log(f"{film} mix (background)")
    mixes.append(subprocess.Popen([sys.executable, "sf.py", film, "mix"], cwd=HERE, env=env,
                                  stdout=open(HERE / f"q_{film}_mix.log", "w", encoding="utf8"), stderr=subprocess.STDOUT))
for m in mixes:
    m.wait()
log("ALL DONE " + str([m.returncode for m in mixes]))
