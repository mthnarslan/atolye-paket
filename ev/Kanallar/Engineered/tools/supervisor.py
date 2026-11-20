"""Long-lived film watcher: sees every film, classifies incidents without an LLM, never exits on an incident.

python supervisor.py              run forever (checks every 60 s); also requeues resumable failures (autoresume.py), --no-resume turns that off
python supervisor.py --prime      mark everything already true as seen, then exit
python supervisor.py --once       one dry check against live data (prints incidents, writes nothing)
python supervisor.py --replay DIR --clock "2026-10-30 18:15" [--from "2026-10-30 10:50"]
                                  replay copies of the logs (DIR/Belgesel_Teslim, DIR/CodexOutputs) minute by minute

A film is in flight when batch.log says a run started and has not exited, or when a drive.py process names it
(started from any stage; arguments are read by position). Liveness is events.jsonl activity (stage 3+) or
voice_progress.json (stages 1-2), counted from the run's start so a fresh restart gets a grace period.
Incident classes (no LLM): stall, stage1_failed / plan_failed / materials_stopped / render_failed /
transport_error / duplicate_job / reaudit_timeout (drive.py exit codes 1-4, 10, 11, 12), retry_burst, mass_exit,
lost_run, expansion_loop, plan_loop, gateway_cooldown, low_ram. Only an exit code outside that set goes to Flash.
One incident = one file in Belgesel_Teslim/incidents and one line on stdout.
"""
import json
import re
import subprocess
import sys
import time
import traceback
from bisect import bisect_right
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"C:\Users\meteh\.gemini\scripts")
sys.path.insert(0, str(Path(__file__).parent))
import autoresume  # noqa: E402

PATHS = {}  # film folder name -> input folder path, as seen on drive.py command lines
CODEX = Path(r"C:\Users\meteh\CodexOutputs")
OUT = Path(r"C:\Users\meteh\Belgesel_Teslim")
SP = Path(__file__).parent
STATE = SP / "supervisor_state.json"

STALL_S = 12 * 60          # no event in stage 3+
VOICE_STALL_S = 20 * 60    # no voice_progress change in stage 1-2
BURST_N, BURST_S = 3, 5 * 60
MASS_N, MASS_S = 3, 60
LOST_S = 5 * 60
EXIT_CLASS = {1: "stage1_failed", 2: "plan_failed", 3: "materials_stopped", 4: "render_failed",
              10: "transport_error", 11: "duplicate_job", 12: "reaudit_timeout", 13: "voice_audit_transport"}
HINT = {
    "voice_audit_transport": "Stage-1 audit unverified only by Gemini transport errors (exit 13): autoresume reruns stage 1 (voice kept, passed segments cached).",
    "stall": "Check the bridge (:8099), gateway cooldowns in events.jsonl and free RAM; resume with drive.py <folder> 3 4 once the cause is gone.",
    "stage1_failed": "Voice stage failed: read the REASON line and voice_audit.json in the run folder; rerun stage 1 (or the audit alone).",
    "plan_failed": "Plan stage failed: read voice_step2_review.json and the REASON line; rerun from stage 2.",
    "materials_stopped": "Stage 3 stopped (unresolved shots or a bridge error): resume from stage 3 and read 03_materials/REPORT.md.",
    "render_failed": "Stage 4 failed: read the last stage-4 error in the queue log; resume from stage 4.",
    "transport_error": "Bridge unreachable or reset (exit 10): check :8099, then resume from the same stage.",
    "duplicate_job": "The bridge already runs this film (exit 11): do not relaunch, wait for the active job.",
    "reaudit_timeout": "Voice re-audit timed out (exit 12): the film is FAILED; rerun the audit alone.",
    "retry_burst": "Stage 3 stopped and was resumed several times within minutes: the cause is not transient; read REPORT.md before another retry.",
    "mass_exit": "Several films exited together: the bridge, the PC or the gateway went down; check the bridge and restart the films one at a time.",
    "lost_run": "batch.log says the film runs but no drive.py names it: its launcher died; relaunch from the stage it reached.",
    "expansion_loop": "Source search expansion keeps repeating; check source_search.json and the sources service.",
    "plan_loop": "Last-resort replans repeat; read plan_review.json.",
    "gateway_cooldown": "Requests waited in a gateway cooldown; check 9router/Gemini key state.",
    "low_ram": "Free RAM under 0.5 GB; do not start another film.",
    "autoresume_capped": "Automatic requeues for this stage are used up (3): read REPORT.md and the queue log, fix the cause, then requeue by hand.",
}
LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (\S+) (.*)$")
_events_cache = {}


def ts(text):
    if text.count(":") == 1:
        text += ":00"
    return time.mktime(time.strptime(text, "%Y-%m-%d %H:%M:%S"))


def stamp(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def key_of(name):
    m = re.match(r"([A-Za-z]+\d+)", name)
    return m.group(1) if m else name


def read_lines(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


def driving():
    """{film folder name: start stage} for the drive.py processes running now, or None if the listing failed."""
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-c",
                              "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | % CommandLine"],
                             capture_output=True, text=True, errors="replace", timeout=60).stdout
    except Exception:
        return None
    if "python" not in out.lower():
        return None
    found = {}
    for line in out.splitlines():
        m = re.search(r'drive\.py"?\s+("[^"]+"|\S+)\s+(\d+)', line)
        if m:
            full = m.group(1).strip('"').replace("\\", "/")
            found[Path(full).name] = int(m.group(2))
            PATHS[Path(full).name] = full
    return found


def free_ram_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 2**30
    except Exception:
        return 99


def film_dirs():
    return {key_of(p.name): p for p in sorted(CODEX.glob("*")) if p.is_dir() and (p / "03_materials").exists()}


def event_times(path):
    """[(epoch, stage, cooldown)] of an events.jsonl, cached by size."""
    try:
        size = path.stat().st_size
    except Exception:
        return []
    hit = _events_cache.get(path)
    if hit and hit[0] == size:
        return hit[1]
    rows = []
    for line in read_lines(path):
        try:
            r = json.loads(line)
            rows.append((datetime.strptime(r["at"], "%Y-%m-%dT%H:%M:%S%z").timestamp(), r.get("stage", ""),
                         float(r.get("cooldown_seconds") or 0)))
        except Exception:
            pass
    _events_cache[path] = (size, rows)
    return rows


def parse_batch(now):
    """Walk batch.log up to `now`: per-film run state, exits and stage-3 retry times."""
    runs, exits, retries = {}, [], {}
    for text in read_lines(OUT / "batch.log"):
        m = LINE.match(text)
        if not m:
            continue
        t = ts(m.group(1))
        if t > now:
            break
        key, rest = key_of(m.group(2)), m.group(3)
        end = start = None
        g = None
        if "start (free RAM" in rest:
            start = 1
        elif re.search(r"manual (?:run|retry) from stage (\d)", rest):
            start = int(re.search(r"manual (?:run|retry) from stage (\d)", rest).group(1))
        elif re.search(r"stopped in stage (\d+), resume from 3", rest):
            end, start = (int(re.search(r"stopped in stage (\d+)", rest).group(1)), "queue"), 3
            retries.setdefault(key, []).append(t)
        elif re.search(r"FAILED at stage (\d+)", rest):
            end = (int(re.search(r"FAILED at stage (\d+)", rest).group(1)), "queue")
        elif rest.rstrip().endswith("DONE"):
            end = (0, "queue")
        elif re.search(r"manual run exit (\d+)", rest):
            end = (int(re.search(r"manual run exit (\d+)", rest).group(1)), "manual")
        if end is not None:
            run = runs.get(key, {})
            run.update(running=False, end=t)
            runs[key] = run
            exits.append({"film": key, "code": end[0], "src": end[1], "at": t, "line": text.strip()})
        if start is not None:
            runs[key] = {"running": True, "start": t, "stage": start, "name": m.group(2)}
    return runs, exits, retries


def evidence(key):
    log = None
    for p in (OUT / "queue").glob(key + "*.log"):
        if not p.name.endswith(("_audit.log", "_graphics.log")):
            log = p
    if not log:
        return ""
    lines = read_lines(log)
    reasons = [l[:300] for l in lines if l.startswith("REASON ")][-3:]
    return "\n".join(reasons + [l[:300] for l in lines[-6:]])


def check(now, live=True, procs=None):
    found = []

    def add(kind, film, detail, key, at):
        found.append({"kind": kind, "film": film, "detail": detail, "key": "%s|%s|%s" % (film, kind, key), "at": at})

    runs, exits, retries = parse_batch(now)
    dirs = film_dirs()
    # a film started outside the logs (by hand, any stage) is still in flight when a drive.py names it
    for name, stage in (procs or {}).items():
        k = key_of(name)
        if not runs.get(k, {}).get("running"):
            runs[k] = {"running": True, "start": runs.get(k, {}).get("end", now), "stage": stage, "name": name}
        runs[k]["proc"] = True
    # several films exiting together is one incident
    mass, cluster = set(), []
    for e in exits + [None]:
        if cluster and (e is None or e["at"] - cluster[-1]["at"] > MASS_S):
            bad = [x for x in cluster if x["code"] != 0]
            if len({x["film"] for x in bad}) >= MASS_N:
                mass.update(id(x) for x in cluster)
                add("mass_exit", "ALL", "films exited together: " + ", ".join("%s=%d" % (x["film"], x["code"]) for x in cluster),
                    stamp(cluster[0]["at"]), cluster[-1]["at"])
            cluster = []
        if e is not None:
            cluster.append(e)
    burst = {}
    for film, times in retries.items():
        for t in times:
            win = [x for x in times if t <= x < t + BURST_S]
            if len(win) >= BURST_N:
                burst.setdefault(film, []).append(win[BURST_N - 1])
                add("retry_burst", film, "%d stage-3 stops resumed within %d s" % (len(win), BURST_S), stamp(win[0]), win[BURST_N - 1])
                break
    for e in exits:
        if e["code"] == 0 or id(e) in mass or "resume from 3" in e["line"]:
            continue
        if any(0 <= e["at"] - b < BURST_S for b in burst.get(e["film"], [])):
            continue  # the burst incident already covers this failure
        add(EXIT_CLASS.get(e["code"], "exit_%d" % e["code"]), e["film"], e["line"], stamp(e["at"]), e["at"])
    # stalls and lost launchers
    for film, run in runs.items():
        if not run.get("running"):
            continue
        d = dirs.get(film)
        evs = event_times(d / "03_materials" / "events.jsonl") if d else []
        i = bisect_right([x[0] for x in evs], now)
        last_ev = evs[i - 1][0] if i else 0
        if run["stage"] >= 3:
            act, limit = max(run["start"], last_ev), STALL_S
        else:
            vp = d / "voice_progress.json" if d else None
            mt = vp.stat().st_mtime if live and vp and vp.exists() else 0
            act, limit = max(run["start"], mt if mt <= now else 0), VOICE_STALL_S
        if now - act > limit and ((live and act > run["start"]) if run["stage"] < 3 else evs):
            add("stall", film, "no activity for %.0f min (stage %s run since %s)" % ((now - act) / 60, run["stage"], stamp(run["start"])),
                int(act), act + limit)
        if live and procs is not None and not run.get("proc") and now - run["start"] > LOST_S:
            add("lost_run", film, "batch.log shows a run since %s but no drive.py names it" % stamp(run["start"]),
                int(run["start"]), run["start"] + LOST_S)
    # event-based loops
    for film, d in dirs.items():
        evs = event_times(d / "03_materials" / "events.jsonl")
        i = bisect_right([x[0] for x in evs], now)
        recent = [x for x in evs[:i] if x[0] >= now - 3600]
        if not recent:
            continue
        cool = [x for x in recent[-400:] if x[2] > 60]
        if cool:
            add("gateway_cooldown", film, "%d requests waited >60 s in a gateway cooldown" % len(cool), stamp(cool[-1][0])[:15], cool[-1][0])
        exp = [x for x in recent if x[1] == "source_search_expansion_started"]
        if len(exp) > 3:
            add("expansion_loop", film, "%d expansion rounds in the last hour" % len(exp), stamp(exp[-1][0]), exp[-1][0])
        last = [x for x in recent if x[1] == "automatic_mix_replan_last_resort"]
        if len(last) > 2:
            add("plan_loop", film, "%d last-resort replans in the last hour" % len(last), stamp(last[-1][0]), last[-1][0])
    if live and free_ram_gb() < 0.5:
        add("low_ram", "PC", "free RAM %.2f GB" % free_ram_gb(), time.strftime("%Y%m%d%H", time.localtime(now)), now)
    return found


def consult(ctx):
    """Flash only, one call, for an exit code no class knows."""
    from documentary_materials.io import api
    q = "A documentary pipeline run exited with an unknown code. Give JSON {\"cause\":string,\"fix_now\":string}. Be brief.\n\n" + ctx
    try:
        return api("flash", q, SP / "incidents" / ("%s_unknown_flash.json" % time.strftime("%H%M%S")), tokens=800, timeout=60)["data"]
    except Exception as exc:
        return {"error": type(exc).__name__}


def resume_step(state, now, procs, report_dir):
    """Requeue films that stopped on a resumable failure (autoresume.py)."""
    runs, exits, _ = parse_batch(now)

    def report(kind, film, detail):
        inc = {"kind": kind, "film": film, "detail": detail, "at": now, "detected": now}
        print("%s INCIDENT %s %s: %s -> %s" % (stamp(now), kind, film, detail, write_incident(inc, report_dir)), flush=True)

    def log_text(film):
        for p in (OUT / "queue").glob(film + "*.log"):
            if not p.name.endswith(("_audit.log", "_graphics.log")):
                return "\n".join(read_lines(p)[-60:])
        return ""

    def log(text, at):
        print("%s %s" % (stamp(at), text), flush=True)
        autoresume.batch_log(text, at)

    autoresume.tick(state, now, runs, exits, procs, log_text, PATHS, report, log=log)


def write_incident(inc, out_dir):
    ev = evidence(inc["film"]) if inc["film"] not in ("ALL", "PC") else ""
    extra = ""
    if inc["kind"].startswith("exit_"):  # a code no class knows
        extra = "\n## Flash\n%s\n" % json.dumps(consult(inc["detail"] + "\n" + ev), ensure_ascii=False, indent=1)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / ("%s_%s_%s.md" % (time.strftime("%Y%m%d_%H%M%S", time.localtime(inc["detected"])), inc["kind"], inc["film"]))
    path.write_text("# %s - %s\n\n%s\n\nEvidence time: %s\n\nSuggested: %s\n\n## Evidence\n```\n%s\n```\n%s" % (
        inc["kind"], inc["film"], inc["detail"], stamp(inc["at"]),
        HINT.get(inc["kind"], "Unknown exit code: read the queue log."), ev, extra), encoding="utf-8")
    return path


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"seen": []}


def save_state(state):
    STATE.write_text(json.dumps(state), encoding="utf-8")


def replay(root, clock, start):
    global OUT, CODEX
    OUT, CODEX = Path(root) / "Belgesel_Teslim", Path(root) / "CodexOutputs"
    end = ts(clock)
    t = ts(start) if start else min(ts(m.group(1)) for m in map(LINE.match, read_lines(OUT / "batch.log")) if m)
    seen, flagged = set(), []
    while t <= end:
        for inc in check(t, live=False):
            if inc["key"] not in seen:
                seen.add(inc["key"])
                flagged.append((t, inc))
        t += 60
    for t, inc in flagged:
        print("%s detected %-18s %-6s evidence %s lag %4.0f s  %s" % (
            stamp(t)[11:16], inc["kind"], inc["film"], stamp(inc["at"])[11:19], t - inc["at"], inc["detail"][:75]))
    print("incidents:", len(flagged), "| LLM calls: 0")


def main():
    state = load_state()
    incidents = OUT / "incidents"
    incidents.mkdir(parents=True, exist_ok=True)
    seen = set(state["seen"])
    if "--keep-history" not in sys.argv:  # what is already true at start is not news
        seen |= {i["key"] for i in check(time.time(), procs=driving())}
        autoresume.prime(state, parse_batch(time.time())[1])  # failures that already happened are not resumed
    while True:
        try:
            now = time.time()
            (SP / "supervisor_heartbeat.txt").write_text(stamp(now))
            procs = driving()
            if "--no-resume" not in sys.argv:
                resume_step(state, now, procs, incidents)
            for inc in check(now, procs=procs):
                if inc["key"] in seen:
                    continue
                seen.add(inc["key"])
                inc["detected"] = now
                path = write_incident(inc, incidents)
                print("%s INCIDENT %s %s: %s -> %s" % (stamp(now), inc["kind"], inc["film"], inc["detail"], path), flush=True)
            state["seen"] = sorted(seen)[-5000:]
            save_state(state)
        except Exception:
            with (SP / "supervisor.err").open("a", encoding="utf-8") as f:
                f.write(stamp(time.time()) + "\n" + traceback.format_exc())
        time.sleep(60)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--prime"]:
        s = load_state()
        s["seen"] = sorted(set(s["seen"]) | {i["key"] for i in check(time.time(), procs=driving())})
        autoresume.prime(s, parse_batch(time.time())[1])
        save_state(s)
        print("primed", len(s["seen"]))
    elif a[:1] == ["--once"]:
        for i in check(time.time(), procs=driving()):
            print(i["kind"], i["film"], i["detail"][:100])
    elif a[:1] == ["--replay"]:
        replay(a[1], a[a.index("--clock") + 1], a[a.index("--from") + 1] if "--from" in a else None)
    else:
        main()
