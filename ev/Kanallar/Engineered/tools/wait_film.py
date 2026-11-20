"""Block until a film (or every active film) needs the commander, then print ONE line and exit.

python wait_film.py <film|all> [--until done|incident|any] [--heartbeat 1800] [--poll 30]
                    [--replay DIR --clock "YYYY-MM-DD HH:MM:SS"] [--root OUT]

Reads files only (no network, no LLM): <OUT>/batch.log and <OUT>/queue/<film>.log written by queue_films.py /
run_when_free2.sh, <CodexOutputs>/<film>/ (run.lock, voice_audit.json, 03_materials/events.jsonl, status.json when it
exists). <film> is a folder name or its prefix (EP05). Known error classes (Arch 4.4: transient_llm, transport,
duplicate_job, voice_text, allocation_short, search_down, glabs_down, resource) are counted and the wait goes on.

Output, one line on stdout:
  WAIT <event> film=<name> stage=<n> class=<class> next=<action> idle=<min> known=<class:count,...>
Exit codes:
  0 done       every watched film delivered (queue log ends with ALL STAGES DONE)
  1 failed     a watched film ended in failure with no retry coming (class + next action printed)
  2 incident   class unknown or code_bug: park the film and wake Claude
  3 heartbeat  nothing terminal for --heartbeat seconds (mandatory; a silent waiter hides stalls)
  4 usage      film not found / bad arguments
--until done: exit on 0/1 only; incident: on 2 only; any (default): on all. Heartbeat always applies.
Replay: --replay DIR (DIR/batch.log, DIR/queue/*.log, optional DIR/CodexOutputs) with --clock = fake "now". Logs are
revealed up to the fake time and the clock advances by --poll per iteration without sleeping.
"""
import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

LIVE_OUT = Path(r"C:\Users\meteh\Belgesel_Teslim")
LIVE_RUN = Path(r"C:\Users\meteh\CodexOutputs")
TS = "%Y-%m-%d %H:%M:%S"
GRACE = 90  # seconds a failed attempt may wait for the queue to restart it before it counts as terminal
STAGE_RE = re.compile(r"^\[stage (\d)\] http=(\S+) status=(\S+)")
EV_RE = re.compile(r"^(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d) (\S+) ?(.*)$")
BUG_RE = re.compile(r"\b(KeyError|TypeError|AttributeError|NameError|IndexError|UnboundLocalError|ZeroDivisionError)\b"
                    r"|WinError 32\b|has an empty name")
CLASSES = [  # first match wins; transport and LLM signals are tested before code_bug
    ("duplicate_job", re.compile(r"already has an active production job", re.I), "attach_to_running_job_no_retry"),
    ("allocation_short", re.compile(r"No feasible narrative/category allocation|ALLOCATION_SHORT", re.I),
     "top_up_short_category_rerun_stage3_once"),
    ("glabs_down", re.compile(r"Max Retries Exceeded", re.I), "restart_glabs_limit_3_parallel"),
    ("transport", re.compile(r"ConnectionRefused|ConnectionReset|URLError|WinError 1005[34]|WinError 10061|WinError 10054"
                             r"|RemoteDisconnected|non-JSON", re.I), "wait_bridge_then_rerun_same_stage"),
    ("transient_llm", re.compile(r"ReadTimeout|\b50[0-9] Server|\b503\b|\b429\b|timed? ?out|PASS_DEGRADED|UNVERIFIED", re.I),
     "rerun_same_stage_after_2_5_15min"),
    ("search_down", re.compile(r"searxng|:8888", re.I), "start_searxng_docker"),
    ("code_bug", BUG_RE, "park_read_traceback_wake_claude"),
]


def to_dt(s):
    return datetime.strptime(s, TS)


class Source:
    """File access; in replay mode every read is limited to what existed at the fake time."""

    def __init__(self, root, runs, replay, clock):
        self.root, self.runs, self.replay = root, runs, replay
        self.clock = clock  # datetime (live: None)
        self._cache = {}

    def now(self):
        return self.clock if self.replay else datetime.now()

    def advance(self, secs):
        if self.replay:
            self.clock += timedelta(seconds=secs)
        else:
            time.sleep(secs)

    def _read(self, path, tail=None):
        try:
            st = path.stat()
            key = (str(path), st.st_mtime_ns, st.st_size, tail)
            if key in self._cache:
                return self._cache[key]
            with open(path, "rb") as f:
                if tail and st.st_size > tail:
                    f.seek(-tail, 2)
                text = f.read().decode("utf-8", errors="replace")
            self._cache = {k: v for k, v in self._cache.items() if k[0] != str(path)}
            self._cache[key] = text
            return text
        except OSError:
            return ""

    def batch_events(self):
        """[(datetime, film token, text)] visible now, oldest first."""
        out = []
        for line in self._read(self.root / "batch.log").splitlines():
            m2 = EV_RE.match(line)
            if not m2:
                continue
            t = to_dt(m2.group(1) + " " + m2.group(2))
            if self.replay and t > self.clock:
                break
            out.append((t, m2.group(3), m2.group(4)))
        return out

    def queue_text(self, film, events):
        """Queue log text visible now. Live: the whole tail. Replay: cut after the k-th failed attempt, where k is the
        number of failed-attempt events (stopped / FAILED / manual exit != 0) logged for the film by the fake time."""
        full = self._read(self.root / "queue" / (film + ".log"), tail=400_000)
        if not self.replay:
            return full
        lines = full.splitlines()
        # A block ends at the error JSON that follows a failing stage line; it is matched to the batch.log failure
        # events by stage number (stopped/FAILED "in stage N", "manual run exit N": drive.py exits with the stage).
        ends, pending, stage_of = [], None, None
        for i, ln in enumerate(lines):
            m = STAGE_RE.match(ln)
            if m:
                bad = m.group(2) != "200" or m.group(3) not in ("PASS", "SUCCESS", "MATERIALS_READY", "PASS_WITH_NOTES")
                pending, stage_of = (int(m.group(1)) if bad else None), int(m.group(1))
            elif pending and ln.startswith("{"):
                ends.append((pending, i + 1))
                pending = None
        count, last_fail = Counter(), None
        for t, tok, txt in events:
            if not self._is_film(tok, film):
                continue
            m = re.search(r"(?:(?:in|at) stage|manual run exit) (\d)", txt)
            if m and ("stopped in stage" in txt or "FAILED at stage" in txt or re.search(r"manual run exit [1-9]", txt)):
                count[int(m.group(1))] += 1
                last_fail = t
        cut, seen = 0, Counter()
        for stg, end in ends:
            seen[stg] += 1
            if seen[stg] <= count[stg]:
                cut = max(cut, end)
        if cut == 0:  # nothing failed yet: show only the lines before the first failing block
            first = next((i for i, ln in enumerate(lines) if STAGE_RE.match(ln) and ln.split("status=")[1].split()[0] == "FAIL"), len(lines))
            return "\n".join(lines[:first])
        while cut < len(lines) and not lines[cut].startswith("[stage"):
            cut += 1  # trailing traceback lines belong to the block
        later_ok = any(t > last_fail and self._is_film(tok, film) and (txt.strip() == "DONE" or "manual run exit 0" in txt)
                       for t, tok, txt in events)
        if later_ok:  # the run after the last failure finished: reveal up to the next failing block
            nxt = next((end - 1 for stg, end in ends if end > cut), len(lines))
            cut = max(cut, min(len(lines), nxt if nxt < len(lines) else len(lines)))
            while cut > 0 and cut < len(lines) and not (lines[cut].startswith("[stage") or lines[cut] == "ALL STAGES DONE"):
                cut += 1
            if "ALL STAGES DONE" in lines[cut:] and not any(e[1] > cut for e in ends):
                cut = len(lines)
        return "\n".join(lines[:cut])

    @staticmethod
    def _is_film(token, film):
        return token == film or film.startswith(token + "_") or token.startswith(film[:4]) and token == film.split("_")[0]

    def run_file(self, film, rel):
        if self.replay and not (self.runs / film).exists():
            return ""
        return self._read(self.runs / film / rel)


def last_attempt(text):
    """(stage, status, error text) of the newest stage line in a queue log, plus whether the log ends done."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    done = bool(lines) and lines[-1].strip() == "ALL STAGES DONE"
    idx = max((i for i, ln in enumerate(lines) if STAGE_RE.match(ln)), default=-1)
    if idx < 0:
        return None, None, "", done
    m = STAGE_RE.match(lines[idx])
    body = "\n".join(lines[idx + 1: idx + 60])
    return int(m.group(1)), m.group(3), (lines[idx] + "\n" + body), done


def classify(stage, status, body, src, film, note=""):
    if stage == 1 and status in ("FAIL", "REVIEW") and '"error_type": null' in body:
        audit = src.run_file(film, "voice_audit.json")
        if '"text_completeness": "FAIL"' in audit and '"reference_voice_match": "PASS"' in audit:
            return "voice_text", "redo_voice_py_then_stage2"
        if re.search(r"ReadTimeout|503|429|unreviewed", note):
            return "transient_llm", "audit_only_rerun_stage1"
        return "unknown", "park_read_voice_audit_json_wake_claude"
    if "unresolved shots" in body:
        return "unresolved_shots", "queue_retries_stage3_else_read_REPORT_md"
    # a traceback is classified by its exception line, so a ConnectionRefused traceback is transport, not code_bug
    tail = body.splitlines()
    exc = [ln for ln in tail if re.match(r"^[A-Za-z_.]*(Error|Exception|Refused|Reset)\b", ln.strip())]
    probe = (exc[-1] + "\n" if exc else "") + body
    for name, rx, action in CLASSES:
        if rx.search(probe if name != "code_bug" else (exc[-1] if exc else body)):
            return name, action
    return "unknown", "park_wake_claude"


def film_state(src, film, events, now):
    """-> dict(state=running|done|failed|incident, stage, cls, next, idle_s, retrying)"""
    mine = [e for e in events if src._is_film(e[1], film)]
    text = src.queue_text(film, events)
    stage, status, body, done = last_attempt(text)
    st = {"stage": stage if stage is not None else "?", "cls": "-", "next": "-", "state": "running", "idle_s": 0}
    last_ev = mine[-1] if mine else None
    ended = status is not None and not (status in ("PASS", "SUCCESS", "MATERIALS_READY", "PASS_WITH_NOTES") and
                                        (stage != 4 or done))
    if done or (last_ev and last_ev[2].strip() == "DONE"):
        st.update(state="done", next="collect_delivery_zip")
    elif ended and status not in ("PASS", "SUCCESS", "MATERIALS_READY", "PASS_WITH_NOTES"):
        cls, action = classify(stage, status, body, src, film, last_ev[2] if last_ev else "")
        st.update(cls=cls, next=action)
        since = (now - last_ev[0]).total_seconds() if last_ev else 0
        retry = last_ev and ("resume from" in last_ev[2] or re.search(r"manual (retry|run) from", last_ev[2]))
        failed_final = last_ev and ("FAILED at stage" in last_ev[2] or re.search(r"manual run exit [1-9]", last_ev[2]))
        if cls in ("unknown", "code_bug") and not (retry and since <= GRACE):
            st["state"] = "incident"
        elif failed_final or (not retry and since > GRACE and not (last_ev and re.search(r" start ", " " + last_ev[2]))):
            st["state"] = "failed"
        else:
            st["state"] = "retrying"
    if last_ev:
        st["idle_s"] = int((now - last_ev[0]).total_seconds())
    return with_status_json(src, film, st)


def with_status_json(src, film, st):
    """status.json (Q3/Q7) wins over log parsing when it exists and parses; absent or broken files change nothing."""
    try:
        j = json.loads(src.run_file(film, "status.json") or "null")
    except ValueError:
        return st
    if not isinstance(j, dict):
        return st
    state = {"delivered": "done", "done": "done", "failed": "failed", "parked": "incident", "running": "running"}.get(
        str(j.get("state") or j.get("status") or "").lower())
    if state:
        st["state"] = state
    st["stage"] = j.get("stage", st["stage"])
    st["cls"] = j.get("class") or j.get("error_class") or st["cls"]
    st["next"] = j.get("next") or j.get("next_action") or st["next"]
    if st["cls"] in ("unknown", "code_bug") and st["state"] != "done":
        st["state"] = "incident"
    return st


def films_in(src, events):
    seen = {}
    for _t, tok, txt in events:
        if re.match(r"^EP\d+", tok) or "_" in tok:
            seen.setdefault(tok, True)
    names = {p.stem for p in (src.root / "queue").glob("*.log") if re.match(r"^EP\d+", p.stem) and "_graphics" not in p.stem}
    full = {}
    for tok in seen:
        hit = [n for n in names if n == tok or n.startswith(tok + "_")]
        full[tok] = hit[0] if hit else tok
    return sorted(set(full.values()) | names)


def resolve(src, arg, events):
    allf = films_in(src, events)
    if arg == "all":
        return allf, True
    hit = [f for f in allf if f == arg or f.startswith(arg + "_") or f.startswith(arg)]
    return hit[:1], False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("film")
    ap.add_argument("--until", choices=("done", "incident", "any"), default="any")
    ap.add_argument("--heartbeat", type=int, default=1800)
    ap.add_argument("--poll", type=int, default=30)
    ap.add_argument("--replay")
    ap.add_argument("--clock")
    ap.add_argument("--root", help="folder with batch.log and queue/ (default Belgesel_Teslim)")
    a = ap.parse_args(argv)
    if bool(a.replay) != bool(a.clock):
        print("WAIT usage film=- stage=- class=- next=--replay_needs_--clock idle=0 known=-")
        return 4
    if a.replay:
        root, runs = Path(a.replay), Path(a.replay) / "CodexOutputs"
        clock = to_dt(a.clock)
    else:
        root, runs, clock = Path(a.root) if a.root else LIVE_OUT, LIVE_RUN, None
    src = Source(root, runs, bool(a.replay), clock)
    start = src.now()
    events = src.batch_events()
    films, is_all = resolve(src, a.film, events)
    if not films:
        print(f"WAIT usage film={a.film} stage=- class=- next=no_queue_log_or_batch_entry idle=0 known=-")
        return 4
    known, counted = Counter(), set()
    watch = None
    while True:
        now = src.now()
        events = src.batch_events()
        states = {f: film_state(src, f, events, now) for f in films}
        if watch is None:  # "all" watches the films that are not already finished when the wait starts
            watch = [f for f in films if states[f]["state"] not in ("done", "failed")] if is_all else films
            if not watch:
                print("WAIT done film=all stage=- class=- next=nothing_active idle=0 known=-")
                return 0
        for f in watch:
            s = states[f]
            if s["state"] == "retrying":
                key = (f, s["cls"], tuple(e[0] for e in events if src._is_film(e[1], f))[-1:])
                if key not in counted:
                    counted.add(key)
                    known[s["cls"]] += 1
        kn = ",".join(f"{k}:{v}" for k, v in sorted(known.items())) or "-"

        def line(ev, f, s):
            return (f"WAIT {ev} film={f} stage={s['stage']} class={s['cls']} next={s['next']} "
                    f"idle={s['idle_s'] // 60}m known={kn}")
        inc = [f for f in watch if states[f]["state"] == "incident"]
        fin = [f for f in watch if states[f]["state"] == "failed"]
        dn = [f for f in watch if states[f]["state"] == "done"]
        if inc and a.until in ("incident", "any"):
            print(line("incident", inc[0], states[inc[0]]))
            return 2
        if a.until in ("done", "any"):
            if fin:
                print(line("failed", fin[0], states[fin[0]]))
                return 1
            if len(dn) == len(watch):
                print(line("done", dn[-1], states[dn[-1]]))
                return 0
        if (now - start).total_seconds() >= a.heartbeat:
            f = max(watch, key=lambda x: states[x]["idle_s"])
            print(line("heartbeat", f, states[f]))
            return 3
        src.advance(a.poll)


if __name__ == "__main__":
    sys.exit(main())
