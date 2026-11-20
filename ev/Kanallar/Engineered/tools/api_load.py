"""How busy each API role was across films: calls, queue wait, run time, peak in flight.

python api_load.py [film output folder ...]   (default: every CodexOutputs folder)

A role whose calls waited in queue had all its slots taken; a role whose
peak in flight stays well under its limit was idle capacity.
"""
import collections
import json
import sys
from datetime import datetime
from pathlib import Path

folders = [Path(p) for p in sys.argv[1:]] or [p for p in Path(r"C:\Users\meteh\CodexOutputs").iterdir() if p.is_dir()]
stats = collections.defaultdict(lambda: {"calls": 0, "fail": 0, "queued": 0.0, "max_queue": 0.0, "run": 0.0})
edges = collections.defaultdict(list)
for folder in folders:
    path = folder / "events.jsonl"
    if not path.exists():
        continue
    for line in path.open(encoding="utf8", errors="replace"):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        kind, role = row.get("stage"), row.get("role")
        if kind not in ("api_request_started", "api_request_finished") or not role:
            continue
        at = datetime.strptime(row["at"][:19], "%Y-%m-%dT%H:%M:%S").timestamp()
        edges[role].append((at, 1 if kind == "api_request_started" else -1))
        if kind == "api_request_finished":
            s = stats[role]
            s["calls"] += 1
            s["fail"] += int(str(row.get("http_status", 200)) != "200")
            q = float(row.get("queue_seconds") or 0)
            s["queued"] += q
            s["max_queue"] = max(s["max_queue"], q)
            s["run"] += float(row.get("seconds") or 0)

print(f"{'role':12} {'calls':>6} {'fail':>5} {'avg run s':>9} {'avg wait s':>10} {'max wait s':>10} {'peak':>5}")
for role, s in sorted(stats.items()):
    level = peak = 0
    for _, d in sorted(edges[role], key=lambda e: (e[0], e[1])):
        level += d
        peak = max(peak, level)
    n = max(1, s["calls"])
    print(f"{role:12} {s['calls']:6} {s['fail']:5} {s['run']/n:9.1f} {s['queued']/n:10.1f} {s['max_queue']:10.1f} {peak:5}")
