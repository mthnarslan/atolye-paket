"""Direct Gemini API keys as an extra Flash lane, with a per-key daily count.

Flash goes through 9router and had no fallback: when 9router errors the
films wait out its cooldown, and when its slots are full they queue. The
user's own Gemini API keys (DOCUMENTARY_GEMINI_KEYS_FILE, lines starting
"AQ." or "AIza" after a "GEMINI" heading) take those requests instead, on
Google's OpenAI-compatible endpoint with DOCUMENTARY_GEMINI_MODEL
(gemini-3.6-flash: 7-14 s on the 2026-10-30 probe, where gemini-3.8-flash
took 40-90 s direct).

Each key/model pair counts its requests per Pacific day (Google's quota
day) in usage.json, shared by every process. A 429 marks the pair spent
until the next Pacific day; a 403 marks the key dead for the day. pick()
returns the live key with the fewest requests today, or None when all are
spent, which leaves the request on 9router as before.
"""
import contextlib
import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
MODEL = os.environ.get("DOCUMENTARY_GEMINI_MODEL", "gemini-3.6-flash")
KEYS_FILE = Path(os.environ.get("DOCUMENTARY_GEMINI_KEYS_FILE", Path.home() / "Desktop" / "KEY.txt"))
STATE = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "documentary_materials" / "gemini_usage.json"
_LOCK = threading.Lock()
_KEYS = None


def keys():
    global _KEYS
    if _KEYS is None:
        found, gemini = [], False
        try:
            for line in KEYS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if "GEMINI" in line.upper():
                    gemini = True
                elif gemini and line.startswith(("AQ.", "AIza")):
                    found.append(line)
        except OSError:
            pass
        _KEYS = found
    return _KEYS


def _day():
    # Google resets Gemini API quotas at midnight Pacific time.
    return (datetime.now(timezone.utc) - timedelta(hours=8)).strftime("%Y-%m-%d")


@contextlib.contextmanager
def _state():
    with _LOCK:
        lock = STATE.with_suffix(".lock")
        STATE.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(200):
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL)
                break
            except FileExistsError:
                if time.time() - lock.stat().st_mtime > 30:
                    with contextlib.suppress(OSError):
                        os.remove(lock)
                time.sleep(0.05)
        else:
            fd = None
        try:
            try:
                data = json.loads(STATE.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            if data.get("day") != _day():
                data = {"day": _day(), "use": {}}
            yield data
            tmp = STATE.with_suffix(".tmp%d" % threading.get_ident())
            tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
            os.replace(tmp, STATE)
        finally:
            if fd is not None:
                os.close(fd)
                with contextlib.suppress(OSError):
                    os.remove(lock)


def _id(i, model):
    # The key itself is never written down: its position and last four characters name it.
    return "%d:%s:%s" % (i + 1, keys()[i][-4:], model)


def _dead(i):
    return "%d:%s:dead" % (i + 1, keys()[i][-4:])


def pick(model=MODEL):
    """(index, key) of the live key with the fewest requests today, counted as used; None when all are spent."""
    if not keys():
        return None
    with _state() as data:
        use = data["use"]
        live = [i for i in range(len(keys()))
                if not use.get(_id(i, model), {}).get("spent") and not use.get(_dead(i))]
        if not live:
            return None
        i = min(live, key=lambda k: use.get(_id(k, model), {}).get("requests", 0))
        row = use.setdefault(_id(i, model), {"requests": 0, "ok": 0})
        row["requests"] += 1
        return i, keys()[i]


def report(i, status, model=MODEL):
    """Record the outcome of a request made with key i: 200, 429 (pair spent today) or 403 (key dead today)."""
    with _state() as data:
        row = data["use"].setdefault(_id(i, model), {"requests": 0, "ok": 0})
        if status == 200:
            row["ok"] += 1
        elif status == 429:
            row["spent"] = True
        elif status in (401, 403):
            data["use"][_dead(i)] = True


def summary():
    """Today's counts, for preflight and reports."""
    with _state() as data:
        rows = {k: v for k, v in data["use"].items() if isinstance(v, dict)}
        dead = sum(1 for k in data["use"] if k.endswith(":dead"))
        return {"day": data["day"], "keys": len(keys()), "dead": dead,
                "spent": sum(1 for v in rows.values() if v.get("spent")),
                "requests": sum(v.get("requests", 0) for v in rows.values()),
                "ok": sum(v.get("ok", 0) for v in rows.values())}


if __name__ == "__main__":
    print(json.dumps(summary(), indent=1))
