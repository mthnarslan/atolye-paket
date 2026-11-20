"""G-Labs guard for the ANIM path: circuit breaker + deterministic unsafe-prompt rewrite.

Installed by one import line in runner.py (`from . import anim_guard`); it wraps
anim._run / anim._run_task / anim.available at import time and leaves anim.py
byte-identical, so no finished ANIM shot changes identity (anim.py is hashed whole
by the wide key and by name in the narrow key).

1. Breaker. "Max Retries Exceeded" is G-Labs' own task error: the account pool is
   spent (per-account 429 "Daily image quota exhausted"; the survivors answer
   "requesting too fast"), every queued task then burns its 3 internal retries.
   After THRESHOLD such failures in a row (no success between) the breaker opens for
   BASE_S * 2**level seconds (cap MAX_S), shared by every process through a state
   file in the slot directory. While open, anim.available() is False and anim._run
   raises AnimFailed at once (no slot taken, nothing submitted), so the runner takes
   its existing fallback (NO_MATCH -> other medium). After the cooldown ONE probe
   request is let through; success closes the breaker, failure reopens it one level
   higher.
2. Unsafe. PUBLIC_ERROR_UNSAFE_GENERATION / DANGEROUS / USER_MINOR ...: the prompt is
   rewritten by a fixed word map (sanitise()) and sent once more; if that is refused
   too, AnimFailed is raised and the prompt is remembered, so the same prompt is
   never sent again.

Off switches: DOCUMENTARY_ANIM_GUARD=0 (everything), DOCUMENTARY_GLABS_BREAKER=0,
DOCUMENTARY_ANIM_SANITISE=0.
"""
import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path

from . import anim

ON = os.environ.get("DOCUMENTARY_ANIM_GUARD", "1") != "0"
BREAKER_ON = os.environ.get("DOCUMENTARY_GLABS_BREAKER", "1") != "0"
SANITISE_ON = os.environ.get("DOCUMENTARY_ANIM_SANITISE", "1") != "0"
THRESHOLD = int(os.environ.get("DOCUMENTARY_GLABS_BREAKER_N", "3"))
BASE_S = float(os.environ.get("DOCUMENTARY_GLABS_BREAKER_BASE_S", "600"))
MAX_S = float(os.environ.get("DOCUMENTARY_GLABS_BREAKER_MAX_S", "7200"))
PROBE_S = float(os.environ.get("DOCUMENTARY_GLABS_BREAKER_PROBE_S", "300"))

_DIR = Path(os.environ.get("DOCUMENTARY_SLOT_DIR", str(anim._Slot.DIR)))
STATE = Path(os.environ.get("DOCUMENTARY_GLABS_BREAKER_FILE", str(_DIR / "glabs_breaker.json")))
UNSAFE_FILE = Path(os.environ.get("DOCUMENTARY_GLABS_UNSAFE_FILE", str(_DIR / "glabs_unsafe.json")))
LOG = STATE.with_suffix(".log")
_LOCK = threading.Lock()

POOL_MARKS = ("max retries exceeded", "quota exhausted", "resource_exhausted", "resource exhausted",
              "temporary limit", "requesting too fast")
REFUSED_MARKS = ("unusual_activity", "unusual activity")
UNSAFE_MARKS = ("unsafe_generation", "violates policy", "sexually_explicit", "dangerous", "reputational",
                "user_minor", "prohibited_content", "image_safety")


def classify(exc_or_text):
    """'down' | 'refused' | 'pool' | 'unsafe' | 'other' for a G-Labs failure."""
    text = str(exc_or_text)
    low = text.lower()
    if "httpconnectionpool" in low or type(exc_or_text).__name__ in ("ConnectionError", "ConnectTimeout"):
        return "down"
    if any(m in low for m in UNSAFE_MARKS):
        return "unsafe"
    if any(m in low for m in REFUSED_MARKS):
        return "refused"
    if any(m in low for m in POOL_MARKS):
        return "pool"
    return "other"


# ---- breaker ---------------------------------------------------------------
def _read():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"streak": 0, "level": 0, "open_until": 0.0, "probe_until": 0.0}


def _write(state):
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_suffix(".tmp%d" % os.getpid())
        tmp.write_text(json.dumps(state), encoding="utf-8")
        os.replace(tmp, STATE)
    except Exception:
        pass


def _log(**kw):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **kw}) + "\n")
    except Exception:
        pass


def is_open(now=None):
    """True while the cooldown runs (hard open)."""
    if not (ON and BREAKER_ON):
        return False
    return (now or time.time()) < _read().get("open_until", 0.0)


def left(now=None):
    return max(0.0, _read().get("open_until", 0.0) - (now or time.time()))


def admit(now=None):
    """(ok, seconds_left, why). After the cooldown the first caller claims the probe."""
    if not (ON and BREAKER_ON):
        return True, 0.0, ""
    now = now or time.time()
    with _LOCK:
        s = _read()
        if now < s.get("open_until", 0.0):
            return False, s["open_until"] - now, "breaker open: " + str(s.get("reason", ""))
        if s.get("open_until", 0.0) > 0:  # cooldown over, half-open
            if now < s.get("probe_until", 0.0):
                return False, s["probe_until"] - now, "breaker probing"
            s["probe_until"] = now + PROBE_S
            _write(s)
            _log(event="probe", level=s.get("level"))
        return True, 0.0, ""


def record_ok():
    if not (ON and BREAKER_ON):
        return
    with _LOCK:
        s = _read()
        if s.get("streak") or s.get("open_until") or s.get("level"):
            _write({"streak": 0, "level": 0, "open_until": 0.0, "probe_until": 0.0})
            if s.get("open_until"):
                _log(event="closed")


def record_failure(kind, detail="", now=None):
    """Count a pool/refused/down failure; open the breaker when the streak is long enough."""
    if not (ON and BREAKER_ON) or kind not in ("pool", "refused", "down"):
        return
    now = now or time.time()
    need = 2 if kind == "refused" else THRESHOLD
    with _LOCK:
        s = _read()
        if now < s.get("open_until", 0.0):
            return  # in-flight tasks finishing while open: do not escalate
        probing = s.get("open_until", 0.0) > 0
        s["streak"] = s.get("streak", 0) + 1
        if probing or s["streak"] >= need:
            if probing:
                s["level"] = s.get("level", 0) + 1
            cool = min(MAX_S, BASE_S * (2 ** s.get("level", 0)) * (0.2 if kind == "down" else 1.0))
            s.update(open_until=now + cool, probe_until=0.0, reason="%s: %s" % (kind, detail[:160]))
            _log(event="open", kind=kind, level=s.get("level", 0), cooldown_s=round(cool), detail=detail[:200])
        _write(s)


# ---- unsafe prompt rewrite -------------------------------------------------
# (pattern, replacement); whole words, case-insensitive, applied in order.
SANITISE_MAP = [
    (r"bod(?:y|ies)|corpses?|victims?|casualt(?:y|ies)", "silhouettes"),
    (r"deaths?|dead|died|dying|fatalit(?:y|ies)", "loss"),
    (r"kill(?:ed|ing|s)?|murder(?:ed|s)?|massacre[sd]?", "affect"),
    (r"blood(?:y|stained)?|gore", "red paint"),
    (r"wound(?:s|ed)?|injur(?:y|ies|ed)", "marked"),
    (r"explosions?|explod(?:e|es|ed|ing)|explosive", "burst of shapes"),
    (r"bombs?|bombing|missiles?", "round shape"),
    (r"weapons?|guns?|rifles?|pistols?|knife|knives|swords?", "tool"),
    (r"destruction|devastation|devastated|destroyed|destroys?|wreckage|carnage", "change"),
    (r"ruined|ruins?|rubble|debris|shattered|crushed", "worn"),
    (r"damaged|damage", "marked"),
    (r"impacts?", "contact"),
    (r"rupture[sd]?", "split"),
    (r"children|kids|boys|girls", "people"),
    (r"child|kid|boy|girl|baby|babies|infants?|toddlers?|teenagers?|minors?|students?", "person"),
    (r"nude|naked|sexy|erotic", "plain figure"),
    (r"war|battle|combat", "conflict"),
    (r"president|prime minister|king|queen|celebrity", "official"),
]
_COMPILED = [(re.compile(r"\b(?:%s)\b" % p, re.I), r) for p, r in SANITISE_MAP]
NEUTRAL_SUFFIX = " Calm, neutral, abstract flat shapes only; no people, no faces, no violence."


def sanitise(prompt):
    """Deterministic rewrite; returns (new_prompt, matched patterns). No hit -> neutral suffix."""
    out, hits = prompt, []
    for rx, rep in _COMPILED:
        out, n = rx.subn(rep, out)
        if n:
            hits.append(rx.pattern.split("(?:")[1].split("|")[0])
    if out == prompt:
        return prompt + NEUTRAL_SUFFIX, ["<suffix>"]
    return out, hits


def _hash(path, prompt):
    return hashlib.sha1((path + "\n" + prompt).encode("utf-8")).hexdigest()[:16]


def _unsafe_load():
    try:
        return json.loads(UNSAFE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _unsafe_save(d):
    try:
        UNSAFE_FILE.parent.mkdir(parents=True, exist_ok=True)
        UNSAFE_FILE.write_text(json.dumps(d), encoding="utf-8")
    except Exception:
        pass


# ---- wrappers --------------------------------------------------------------
_orig = {"run": anim._run, "task": anim._run_task, "available": anim.available}


def _refuse(path, left_s, why):
    return anim.AnimFailed("G-Labs %s: refused locally (%s, %.0f s left), nothing submitted" % (path, why, left_s))


def guarded_run(path, body, timeout, shot_dir=None):
    ok, left_s, why = admit()
    if not ok:
        raise _refuse(path, left_s, why)
    return _orig["run"](path, body, timeout, shot_dir)


def guarded_task(path, body, timeout):
    if is_open():  # the breaker opened while this call waited for its slot
        raise _refuse(path, left(), "breaker open")
    known = _unsafe_load() if SANITISE_ON else {}
    prompt = body.get("prompt", "")
    h = _hash(path, prompt)
    if SANITISE_ON and known.get(h) == "dead":
        raise anim.AnimFailed("G-Labs %s: UNSAFE prompt refused before (remembered), not sent again" % path)
    if SANITISE_ON and known.get(h) == "rewrite":
        body = {**body, "prompt": sanitise(prompt)[0]}
    try:
        got = _orig["task"](path, body, timeout)
    except Exception as exc:
        kind = classify(exc)
        if kind == "unsafe" and SANITISE_ON and known.get(h) != "rewrite":
            new, words = sanitise(prompt)
            known[h] = "rewrite"
            _unsafe_save(known)
            _log(event="unsafe_rewrite", path=path, words=words)
            try:
                got = _orig["task"](path, {**body, "prompt": new}, timeout)
            except Exception as exc2:
                if classify(exc2) == "unsafe":
                    known[h] = "dead"
                    _unsafe_save(known)
                    raise anim.AnimFailed("G-Labs %s: UNSAFE even after rewrite (%s)" % (path, words)) from exc2
                record_failure(classify(exc2), str(exc2))
                raise
            record_ok()
            return got
        if kind == "unsafe" and SANITISE_ON:
            known[h] = "dead"
            _unsafe_save(known)
        record_failure(kind, str(exc))
        raise
    record_ok()
    return got


def guarded_available():
    if is_open():
        return False
    return _orig["available"]()


def install():
    if not ON:
        return
    anim._run = guarded_run
    anim._run_task = guarded_task
    anim.available = guarded_available


def uninstall():
    anim._run, anim._run_task, anim.available = _orig["run"], _orig["task"], _orig["available"]


install()
