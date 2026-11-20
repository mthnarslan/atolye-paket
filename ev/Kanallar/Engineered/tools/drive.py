"""Run bridge stages in order like the Dify workflow, but stop at the first failure.

python drive.py <folder> [start=1] [end=4] [profile]

Exit codes: 0 done; 1-4 the stage that failed (its own verdict or an HTTP error from the bridge);
10 transport (connection refused/reset, time-out, non-JSON body, or a silent film folder for DRIVE_STALL s); 11 the bridge already runs a job
for this folder; 12 the stage-1 audit-only rerun timed out; 13 the stage-1 audit ended unverified only because Gemini
transport failed (503/429/time-out in some segments, none judged bad): safe to rerun stage 1, the voice is kept.
Every failure prints one line "REASON <class> <text>" before the exit.
DRIVE_BRIDGE_URL overrides the bridge endpoint (default http://127.0.0.1:8099/run).
"""
import http.client, json, os, re, socket, subprocess, sys, threading, time, urllib.parse
from pathlib import Path

# Defaults are production; the overrides exist for the stub-server test (testbench\drive_stub).
AUDIT = Path(os.environ.get("DRIVE_AUDIT", r"C:\Users\meteh\.gemini\scripts\documentary_voice_audit.py"))
CODEX_OUT = Path(os.environ.get("DRIVE_CODEX_OUT", r"C:\Users\meteh\CodexOutputs"))
HTTP_TIMEOUT = float(os.environ.get("DRIVE_HTTP_TIMEOUT", 24 * 3600))
REAUDIT_TIMEOUT = float(os.environ.get("DRIVE_REAUDIT_TIMEOUT", 1800))
REAUDIT_PAUSE = float(os.environ.get("DRIVE_REAUDIT_PAUSE", 60))
BRIDGE = os.environ.get("DRIVE_BRIDGE_URL", "http://127.0.0.1:8099/run")
FOLDER = sys.argv[1]
START = int(sys.argv[2]) if len(sys.argv) > 2 else 1
END = int(sys.argv[3]) if len(sys.argv) > 3 else 4
PROFILE = sys.argv[4] if len(sys.argv) > 4 else None
OK = {1: {"SUCCESS", "PASS"}, 2: {"PASS"}, 3: {"MATERIALS_READY"}, 4: {"PASS", "PASS_WITH_NOTES"}}
DUPLICATE = "already has an active production job"
HEARTBEAT = float(os.environ.get("DRIVE_HEARTBEAT", 300))  # seconds between reaudit / wait log lines
# The bridge answers /run only when the stage ends (hours), so a reset connection looks like a long wait
# (EP09 hung ~1 h, 2026-10-30). Two guards: TCP keepalive finds a dead peer in ~1-2 min; a film-folder
# activity watchdog ends a wait in which nothing in the film folder changed for STALL seconds (exit 10).
KEEPALIVE_S = float(os.environ.get("DRIVE_KEEPALIVE", 30))
STALL = float(os.environ.get("DRIVE_STALL", 90 * 60))
# Transport recovery (darbogaz_1107 F): a reset/refused connection no longer ends the film step at once. The bridge
# runs a stage inside the HTTP handler, so a reset means either the bridge restarted (job gone, finished work is kept
# on disk) or only the socket died (job may still run: the re-POST then answers "active production job"). Both are
# handled by waiting for /health, then re-POSTing the same stage (idempotent: finished shots/chunks are reused);
# a "still active" answer is joined by waiting with backoff until the old job ends.
RECOVER = float(os.environ.get("DRIVE_RECOVER", 900))        # max seconds to wait for /health after a lost connection
JOIN_MAX = float(os.environ.get("DRIVE_JOIN_MAX", 3 * 3600))  # max seconds to wait for a still-running job of this folder
RECOVER_TRIES = int(os.environ.get("DRIVE_RECOVER_TRIES", 4))  # lost connections tolerated per stage
TRANSIENT_HTTP = (502, 503, 504)


def set_aside_unresolved():
    """A shot that ended unresolved has used its repair rounds; a rerun would REUSE that result (and a repair_N
    result), so it moves them aside. rejected.json stays: the fresh attempt never sees the refused clips again.
    The retry count stays bounded by autoresume's cap per film and stage."""
    shots = CODEX_OUT / Path(FOLDER).name / "03_materials" / "shots"
    tag, moved = time.strftime("%m%d_%H%M"), []
    for rj in sorted(shots.glob("*/result.json")):
        try:
            status = json.loads(rj.read_text(encoding="utf-8")).get("status")
        except (OSError, ValueError):
            continue
        if status in ("PASS", "PASS_WITH_WARNINGS"):
            continue
        for f in [rj, *rj.parent.glob("repair_*/result.json")]:
            f.replace(f.with_name(f"result.before_auto_{tag}.json"))
        moved.append(rj.parent.name)
    return f" (set aside for a fresh try: shots {','.join(moved)})" if moved else ""


def fail(code, cls, text):
    print(f"REASON {cls} {' '.join(str(text).split())[:1500]}", flush=True)
    sys.exit(code)


def reaudit(status):
    """A Gemini 503 can leave part of the voice unreviewed (EP08, 2026-10-30). Rerun the
    audit alone (~3 min) instead of failing the film into redoing 30-80 min of speech.
    Only a full PASS from the same judge lets the film go on."""
    manifest = CODEX_OUT / Path(FOLDER).name / "voice_manifest.json"
    for attempt in range(3):
        if not manifest.exists():
            break
        time.sleep(REAUDIT_PAUSE * (1, 3, 7)[attempt])  # 1, 3, 7 min: a busy Gemini needs time
        started = time.time()
        # output goes to our stdout (the queue log); a heartbeat line every 5 minutes shows it is alive
        proc = subprocess.Popen([sys.executable, str(AUDIT), str(manifest)], cwd=AUDIT.parent, stdout=sys.stdout, stderr=sys.stderr)
        while True:
            try:
                proc.wait(timeout=HEARTBEAT)
                break
            except subprocess.TimeoutExpired:
                waited = time.time() - started
                if waited > REAUDIT_TIMEOUT:
                    proc.kill()
                    proc.wait()
                    fail(12, "reaudit_timeout", f"audit-only rerun {attempt + 1} still running after {waited:.0f}s")
                print(f"[stage 1] audit-only rerun {attempt + 1} running {waited:.0f}s", flush=True)
        status = json.loads((manifest.parent / "voice_audit.json").read_text(encoding="utf-8")).get("verdict")
        print(f"[stage 1] audit-only rerun {attempt + 1}: {status}", flush=True)
        if status == "PASS":
            return "PASS", True
        if status not in ("PASS_DEGRADED", "UNVERIFIED") and not audit_transport_only():
            # Rechecking unchanged audio cannot fix a judged content failure.
            print(f"[stage 1] audit-only rerun {attempt + 1}: content failure, no more reruns", flush=True)
            break
    return status, False


TRANSIENT_HTTP = {408, 425, 429, 500, 502, 503, 504}
TRANSIENT_ERR = {"ReadTimeout", "ConnectTimeout", "Timeout", "ConnectionError", "ChunkedEncodingError",
                 "TimeoutExpired", "SSLError", "ProxyError", "TimeoutError"}


def _transient(item):
    kind, detail = item.get("error_type"), str(item.get("error_detail") or "")
    if kind == "HTTPError":
        m = re.match(r"\s*(\d{3})\b", detail)
        return bool(m) and int(m.group(1)) in TRANSIENT_HTTP
    return kind in TRANSIENT_ERR or "No live Gemini key" in detail


def audit_transport_only():
    """True when voice_audit.json is not a pass only because Gemini calls failed (transport), and no
    segment that WAS judged said anything but PASS. A real content FAIL/REVIEW, hard errors or an
    unparseable reply never count, so they still end the film as before."""
    try:
        a = json.loads((CODEX_OUT / Path(FOLDER).name / "voice_audit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if a.get("hard_errors") or a.get("verdict") == "FAIL":
        return False
    g = a.get("gemini_audio") or {}
    if g.get("verdict") == "FAIL":
        return False
    segs = g.get("segments") or []
    if segs:
        if any(s.get("reviewed", True) and (s.get("reference_voice_match") != "PASS"
               or s.get("text_completeness") != "PASS") for s in segs):
            return False
        bad = [s for s in segs if not s.get("reviewed", True)]
        return bool(bad) and all(_transient(s) for s in bad)
    return a.get("verdict") == "UNVERIFIED" and _transient(a)


def audit_checks():
    """The failing parts of voice_audit.json, for the stage-1 REASON line."""
    try:
        a = json.loads((CODEX_OUT / Path(FOLDER).name / "voice_audit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    bad = {k: v for k, v in (a.get("criteria") or {}).items() if v != "PASS"}
    return f" criteria={bad} hard_errors={a.get('hard_errors')} integrity_defects={a.get('integrity_defects')}"


def newest_mtime():
    """Newest modification time in the film's run folder, two levels deep (events.jsonl, voice_progress.json, shots, chunks)."""
    root = CODEX_OUT / Path(FOLDER).name
    best = 0.0
    try:
        for e in os.scandir(root):
            best = max(best, e.stat().st_mtime)
            if e.is_dir(follow_symlinks=False):
                for e2 in os.scandir(e.path):
                    best = max(best, e2.stat().st_mtime)
    except OSError:
        pass
    return best


def post(stage, out):
    """Blocking POST in a worker thread: out gets (code, raw) or an exception. TCP keepalive on the socket."""
    u = urllib.parse.urlsplit(BRIDGE)
    try:
        conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=HTTP_TIMEOUT)
        conn.connect()
        try:
            conn.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            if hasattr(conn.sock, "ioctl"):  # Windows: idle ms before the first probe, ms between probes
                conn.sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, int(KEEPALIVE_S * 1000), 10000))
        except OSError:
            pass
        conn.request("POST", u.path or "/", headers={"Content-Type": "application/json"},
                     body=json.dumps({"stage": stage, "folder_path": FOLDER, **({"profile": PROFILE} if PROFILE else {})}).encode())
        r = conn.getresponse()
        out.append((r.status, r.read()))
    except BaseException as e:  # reported to the main thread
        out.append(e)


def _health_ok():
    u = urllib.parse.urlsplit(BRIDGE)
    try:
        c = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=5)
        c.request("GET", "/health")
        r = c.getresponse(); r.read(); c.close()
        return r.status == 200
    except OSError:
        return False
    except http.client.HTTPException:
        return False


def wait_health(stage, why):
    """Backoff 1,2,4..15 s until the bridge answers /health (restart takes ~2 min); False after RECOVER seconds."""
    t0, delay = time.time(), 1.0
    print(f"[stage {stage}] connection lost ({why}); waiting up to {RECOVER:.0f}s for the bridge", flush=True)
    while time.time() - t0 < RECOVER:
        if _health_ok():
            print(f"[stage {stage}] bridge back after {time.time() - t0:.0f}s, re-posting the stage", flush=True)
            return True
        time.sleep(delay)
        delay = min(delay * 2, 15.0)
    return False


def call_once(stage):
    """POST one stage; return ('ok', code, body) or ('transport', exception). Silent film folder exits 10."""
    out = []
    t0 = next_beat = time.time()
    next_beat += HEARTBEAT
    threading.Thread(target=post, args=(stage, out), daemon=True).start()
    while not out:
        time.sleep(0.5)
        now = time.time()
        if now >= next_beat and not out:
            next_beat = now + HEARTBEAT
            quiet = now - max(newest_mtime(), t0)
            print(f"[stage {stage}] waiting {now - t0:.0f}s, folder quiet {quiet:.0f}s", flush=True)
            if quiet > STALL:
                fail(10, "stalled", f"stage {stage}: no change in the film folder for {quiet:.0f}s while waiting for the bridge (limit {STALL:.0f}s)")
    res = out[0]
    if isinstance(res, BaseException):
        return ("transport", res)
    return ("ok", res[0], res[1])


def call(stage):
    """POST one stage with transport recovery; return (http code, body)."""
    lost, joined_at, join_n = 0, None, 0
    while True:
        r = call_once(stage)
        if r[0] == "transport":
            e = r[1]
            lost += 1
            if lost > RECOVER_TRIES or not wait_health(stage, f"{type(e).__name__}: {e}"):
                fail(10, "transport", f"stage {stage}: {type(e).__name__}: {e} (recovery tries {lost - 1}/{RECOVER_TRIES}, waited for /health up to {RECOVER:.0f}s)")
            continue
        _, code, raw = r
        try:
            body = json.loads(raw or b"{}")
            if not isinstance(body, dict):
                raise ValueError("body is not an object")
        except ValueError:
            if code in TRANSIENT_HTTP and lost < RECOVER_TRIES:  # gateway-style HTML 502/503 page in front of the bridge
                lost += 1
                time.sleep(min(5 * lost, 30))
                continue
            fail(10, "non_json", f"stage {stage}: http={code} body={raw[:300]!r}")
        if lost and DUPLICATE in str(body.get("error") or ""):
            # We lost the socket but the old job still holds the folder: join it by waiting, then the re-POST resumes.
            joined_at = joined_at or time.time()
            if time.time() - joined_at > JOIN_MAX:
                return code, body  # main loop reports exit 11
            join_n += 1
            if join_n == 1 or join_n % 10 == 0:
                print(f"[stage {stage}] job of this folder still running on the bridge; joining (wait {time.time() - joined_at:.0f}s)", flush=True)
            time.sleep(min(10 + 5 * join_n, 60))
            continue
        return code, body


for stage in range(START, END + 1):
    started = time.time()
    code, body = call(stage)
    status = body.get("status") or body.get("verdict")
    print(f"[stage {stage}] http={code} status={status} next={body.get('next_step_allowed')} "
          f"{time.time() - started:.0f}s", flush=True)
    if DUPLICATE in str(body.get("error") or ""):
        fail(11, "duplicate_job", f"stage {stage}: {body.get('error')}")
    if stage == 1 and code == 200 and (status in ("PASS_DEGRADED", "UNVERIFIED")
                                      or (status == "REVIEW" and audit_transport_only())):
        status, body["next_step_allowed"] = reaudit(status)
    if code != 200 or status not in OK[stage] or body.get("next_step_allowed") is False:
        print(json.dumps({k: body.get(k) for k in ("error_type", "error", "summary", "unresolved", "review")},
                         ensure_ascii=False, default=str)[:3000], flush=True)
        reason = f"stage {stage}: http={code} status={status} next={body.get('next_step_allowed')}"
        if body.get("error"):
            reason += f" {body.get('error_type')}: {body.get('error')}"
        if stage == 1:
            reason += audit_checks()
            if audit_transport_only():
                fail(13, "voice_audit_transport", reason)
        if stage == 3 and "unresolved shots" in str(body.get("error") or ""):
            reason += set_aside_unresolved()
        fail(stage, f"stage{stage}_fail", reason)
print("ALL STAGES DONE", flush=True)
