"""Automatic continuation for supervisor.py: a film that stopped on a resumable failure is requeued from the failed stage.

Resumable (drive.py exit codes, see drive.py):
  2 plan, 3 materials ("N unresolved shots", "No feasible allocation"), 4 render -> same stage again
  10 transport / silent bridge            -> the stage named in the REASON line (else the stage the run started at)
  11 duplicate_job (bridge holds a dead job) -> wait, then try again (see below)
  13 voice_audit_transport (stage-1 audit unverified only because Gemini calls failed) -> stage 1 again; the voice is
     kept (_reusable_generated_result) and passed segments come from the audit cache, so only missing segments are re-sent
Not resumable (an incident is written by supervisor.py, nothing is requeued): 1 voice stage (a judge verdict; a redo costs
30-80 min and would loop), 12 voice re-audit timeout, unknown codes, mass_exit, stalls.

Caps: CAP (3) requeues per film and stage, with growing waits (RETRY_WAIT 2/5/15 min, DUP_WAIT 10/20/30 min). At the cap
the film is left alone, one "autoresume_capped" incident is written and a line goes to batch.log. No loop.

duplicate_job: never restart the bridge while any other film works. Choice made here: first wait and retry (the dead job
often ends by itself); after the cap, restart the bridge ONLY when no drive.py runs, no film folder changed in the last
BRIDGE_IDLE_S seconds and no requeue is pending, then give that film one more try. Switch off with AUTORESUME_BRIDGE_RESTART=0.

Launcher: run_when_free2.sh (same arguments as run_when_free.sh; admits one film at a time, 4 films, 4 GB RAM), started
detached so it waits for capacity by itself. Everything is logged to batch.log as "<name> autoresume ..." lines.
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path

CAP = int(os.environ.get("AUTORESUME_CAP", 3))
RETRY_WAIT = (120, 300, 900)
DUP_WAIT = (600, 1200, 1800)
BRIDGE_IDLE_S = 300
PENDING_TTL = 6 * 3600
RESUMABLE = {2: 2, 3: 3, 4: 4}      # exit code -> stage
BASH = r"C:\Program Files\Git\bin\bash.exe"
LAUNCHER = os.environ.get("AUTORESUME_LAUNCHER", str(Path(__file__).with_name("run_when_free2.sh")).replace("\\", "/"))
CODEX = Path(r"C:\Users\meteh\CodexOutputs")
OUT = Path(r"C:\Users\meteh\Belgesel_Teslim")


def stamp(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def last_reason(log_text):
    """(stage or None, text) of the last REASON line of a queue log."""
    for line in reversed(log_text.splitlines()):
        if line.startswith("REASON "):
            m = re.search(r"\bstage (\d)\b", line)
            return (int(m.group(1)) if m else None), line[:200]
    return None, ""


def classify(code, run, log_text):
    """-> (kind, stage, why). kind: resume | duplicate | no."""
    rstage, rtext = last_reason(log_text)
    if code == 13:
        return "resume", 1, rtext or "exit 13"
    if code in RESUMABLE:
        return "resume", RESUMABLE[code], rtext or "exit %d" % code
    if code in (10, 11):
        stage = rstage or (run or {}).get("stage")
        if not isinstance(stage, int):
            return "no", None, "exit %d but the stage is unknown" % code
        return ("duplicate" if code == 11 else "resume"), stage, rtext or "exit %d" % code
    return "no", None, "exit %d is not resumable" % code


def folder_for(name, paths):
    """The input folder drive.py needs: seen on a command line, else voice_manifest.json, else the run folder."""
    if paths.get(name) and Path(paths[name]).exists():
        return paths[name]
    try:
        m = json.loads((CODEX / name / "voice_manifest.json").read_text(encoding="utf-8"))
        if m.get("input_folder") and Path(m["input_folder"]).exists():
            return m["input_folder"]
    except Exception:
        pass
    return str(CODEX / name) if (CODEX / name).exists() else None


def launch(folder, stage):
    """Start the launcher detached (it waits for free capacity itself)."""
    flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([BASH, LAUNCHER, folder, str(stage)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, creationflags=flags, cwd=str(Path(LAUNCHER).parent))


def batch_log(text, now):
    with (OUT / "batch.log").open("a", encoding="utf-8") as f:
        f.write("%s %s\n" % (stamp(now), text))


def recent_activity(now, window=BRIDGE_IDLE_S):
    """True when any film folder changed within `window` seconds (two levels deep)."""
    try:
        for d in CODEX.iterdir():
            if not d.is_dir():
                continue
            for e in os.scandir(d):
                if now - e.stat().st_mtime < window:
                    return True
                if e.is_dir(follow_symlinks=False):
                    for e2 in os.scandir(e.path):
                        if now - e2.stat().st_mtime < window:
                            return True
    except OSError:
        return True
    return False


def restart_bridge():
    """Stop the bridge process and start it again; bridge_watchdog.sh may do the same, so look at /health first."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ? { $_.CommandLine -match 'documentary_native_bridge' } "
          "| % { Stop-Process -Id $_.ProcessId -Force }; Start-Sleep 90; "
          "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 http://127.0.0.1:8099/health).Content -match 'PASS' } catch { $false }")
    up = subprocess.run(["powershell", "-NoProfile", "-c", ps], capture_output=True, text=True, timeout=200).stdout.strip()
    if up != "True":
        subprocess.run(["powershell", "-NoProfile", "-c",
                        "$env:PYTHONIOENCODING='utf-8'; Start-Process python -WorkingDirectory C:\\Users\\meteh\\.gemini\\scripts -WindowStyle Hidden "
                        "-ArgumentList 'documentary_native_bridge.py' -RedirectStandardOutput C:\\Users\\meteh\\.gemini\\scripts\\bridge_auto.log "
                        "-RedirectStandardError C:\\Users\\meteh\\.gemini\\scripts\\bridge_auto.err.log"], timeout=60)


def prime(state, exits):
    """What already happened is not ours to resume."""
    h = set(state.setdefault("handled", []))
    h |= {"%s|%d" % (e["film"], e["at"]) for e in exits}
    state["handled"] = sorted(h)[-3000:]


def tick(state, now, runs, exits, procs, log_text_of, paths, report, launcher=launch, restarter=restart_bridge, log=batch_log):
    """One pass. state is persisted by the caller. report(kind, film, detail) writes an incident for a cap hit.
    procs: {film folder name: stage} of running drive.py, or None when the listing failed (then nothing is launched)."""
    handled = set(state.setdefault("handled", []))
    counts = state.setdefault("resume_counts", {})
    pending = state.setdefault("resume_pending", {})
    busy = {k.split("_")[0] for k in (procs or {})}
    for e in exits:
        hid = "%s|%d" % (e["film"], e["at"])
        if hid in handled:
            continue
        handled.add(hid)
        film, code = e["film"], e["code"]
        if code == 0 or "resume from 3" in e["line"] or e["src"] not in ("queue", "manual"):
            continue
        run = runs.get(film) or {}
        if run.get("running") or film in pending or film in busy:
            continue
        kind, stage, why = classify(code, run, log_text_of(film))
        name = run.get("name") or film
        if kind == "no":
            log("%s autoresume: not resumable (%s); left for you" % (name, why), now)
            continue
        ck = "%s|%d%s" % (film, stage, "|dup" if kind == "duplicate" else "")
        n = counts.get(ck, 0)
        if n >= CAP:
            extra = ""
            if (kind == "duplicate" and os.environ.get("AUTORESUME_BRIDGE_RESTART", "1") != "0"
                    and not counts.get("bridge_restarted|" + film)):
                if procs == {} and not recent_activity(now) and not pending:
                    log("%s autoresume: duplicate_job cap reached, no other film runs -> restarting the bridge once" % name, now)
                    counts["bridge_restarted|" + film] = 1
                    restarter()
                    pending[film] = {"name": name, "stage": stage, "due": now + 30, "kind": kind, "why": why, "n": CAP}
                    continue
                extra = " (bridge not restarted: other work is running or the process listing failed)"
            log("%s autoresume: STOP, %d requeues from stage %d used (%s)%s; left for you" % (name, n, stage, why[:120], extra), now)
            report("autoresume_capped", film, "stage %d, %d requeues used, last failure: %s%s" % (stage, n, why, extra))
            continue
        wait = (DUP_WAIT if kind == "duplicate" else RETRY_WAIT)[min(n, 2)]
        pending[film] = {"name": name, "stage": stage, "due": now + wait, "kind": kind, "why": why, "n": n + 1}
        counts[ck] = n + 1
        log("%s autoresume: will requeue from stage %d in %d s (try %d/%d after %s)" % (name, stage, wait, n + 1, CAP, why[:120]), now)
    state["handled"] = sorted(handled)[-3000:]
    for film, p in list(pending.items()):
        r = runs.get(film) or {}
        if p.get("launched"):
            if r.get("start", 0) > p["launched"] or now - p["launched"] > PENDING_TTL:
                del pending[film]
            continue
        if r.get("running") or film in busy:
            del pending[film]  # someone started it meanwhile
            continue
        if now < p["due"] or procs is None:
            continue
        folder = folder_for(p["name"], paths)
        if not folder:
            log("%s autoresume: input folder not found; left for you" % p["name"], now)
            del pending[film]
            continue
        launcher(folder, p["stage"])
        p["launched"] = now
        log("%s autoresume: queued from stage %d via run_when_free2.sh (try %d/%d)" % (p["name"], p["stage"], p["n"], CAP), now)
