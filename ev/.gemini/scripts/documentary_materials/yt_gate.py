"""One pace for every YouTube request of the process, whichever film makes it.

Four films in one bridge each ran their own searches, probes and
downloads at full speed: a parallel run of four sent several hundred
yt-dlp requests in its first minutes, and YouTube answered "Sign in to
confirm you're not a bot" three minutes in (PAR_1..4, 2026-10-27). Each
film then kept asking: 402 bot refusals in the second run, 303 of them
full-file downloads walking the height ladder of a source whose windows
had just been refused.

Every yt-dlp call that reaches YouTube goes through call() here: a token
bucket (DOCUMENTARY_YT_RPM requests a minute, 10 by default, 41.7 with
DOCUMENTARY_YT_COOKIES_BROWSER set; bursts of
DOCUMENTARY_YT_BURST) and at most DOCUMENTARY_YT_CONCURRENCY calls at a
time, for all films together. A refusal (bot check, HTTP 429, HTTP 403,
"rate-limited") pauses every YouTube call of the process, and of any
other process sharing the cache folder, for 2, 4, 8 ... minutes, up to
DOCUMENTARY_YT_BACKOFF_MAX_SECONDS; the call that was refused is tried
once more after the pause. The pause is logged as "youtube_backoff" in
the film that hit it and "youtube_paused" in every film that waited.

The bridge reloads this module before every stage request. A reload
re-runs the module in the same namespace, so the state below is kept
from the first load: the films share one bucket whichever code version
their threads run. The bucket itself lives in the cache folder
(bucket.json), so the production bridge and a test bridge running at the
same time keep to one budget instead of two.
"""
import contextlib
import json
import os
import threading
import time
from pathlib import Path

from .control import check_cancelled
from .io import event

# Optional YouTube account cookies, "browser[:profile]" (e.g.
# "firefox:yt-dlp"); off by default. Use a profile kept for yt-dlp only.
COOKIES_BROWSER = os.environ.get("DOCUMENTARY_YT_COOKIES_BROWSER", "").strip()
# yt-dlp's wiki puts YouTube's limit at about 1000 page and player
# requests an hour logged out and 4000 with an account; the defaults keep
# to about 60 percent of that: 600/h (10 a minute) and 2500/h.
RPM = max(1.0, float(os.environ.get("DOCUMENTARY_YT_RPM") or (2500 / 60 if COOKIES_BROWSER else 600 / 60)))
BURST = max(1, int(os.environ.get("DOCUMENTARY_YT_BURST", "6")))
CONCURRENCY = max(1, int(os.environ.get("DOCUMENTARY_YT_CONCURRENCY", "3")))
BACKOFF_SECONDS = float(os.environ.get("DOCUMENTARY_YT_BACKOFF_SECONDS", "120"))
BACKOFF_MAX_SECONDS = float(os.environ.get("DOCUMENTARY_YT_BACKOFF_MAX_SECONDS", "1800"))
# A call that has waited this long for the gate gives up, so a film whose
# YouTube is blocked for hours fails its sources instead of hanging.
MAX_WAIT_SECONDS = float(os.environ.get("DOCUMENTARY_YT_MAX_WAIT", "3600"))
# Tries of a refused call after the pause it caused.
BLOCK_RETRIES = max(0, int(os.environ.get("DOCUMENTARY_YT_BLOCK_RETRIES", "1")))

CACHE_DIR = Path(os.environ.get("DOCUMENTARY_YT_CACHE")
                 or Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
                 / "documentary_materials" / "yt_cache")

# "Sign in to confirm your age" is an age gate, not a refusal, so the bot
# check is matched on its own words.
_REFUSALS = ("not a bot", "HTTP Error 429", "Too Many Requests", "HTTP Error 403",
             "rate-limited", "rate limited")


class YouTubeBlocked(RuntimeError):
    """The gate stayed closed for longer than MAX_WAIT_SECONDS."""


_S = globals().get("_S")
if _S is None:
    _S = {"cond": threading.Condition(), "tokens": float(BURST), "stamp": time.monotonic(),
          "active": 0, "until": 0.0, "streak": 0, "paused_at": 0.0, "noticed": set(),
          "disk": (None, 0.0), "calls": {}}


def throttled(exc):
    """True when YouTube refused the request rather than the video."""
    text = str(exc)
    return any(k in text for k in _REFUSALS)


def _pause_file():
    return CACHE_DIR / "backoff.json"


def _disk_until():
    """The pause another process wrote, read again only when the file changed."""
    try:
        stamp = _pause_file().stat().st_mtime_ns
    except OSError:
        return 0.0
    seen, until = _S["disk"]
    if stamp != seen:
        try:
            until = float(json.loads(_pause_file().read_text(encoding="utf-8")).get("until") or 0)
        except (OSError, ValueError):
            until = 0.0
        _S["disk"] = (stamp, until)
    return until


def _film(out):
    if out is not None:
        return Path(out)
    from . import control
    return getattr(control._local, "out", None)


def paused_for():
    """Seconds left of the current pause, 0 when YouTube is open."""
    with _S["cond"]:
        return max(0.0, max(_S["until"], _disk_until()) - time.time())


def wait_clear(out=None):
    """Wait out a pause without taking a request slot (CDN reads, storyboards)."""
    _wait(out, take=False)


def _wait(out, take):
    out = _film(out)
    started = time.monotonic()
    cond = _S["cond"]
    with cond:
        while True:
            now = time.time()
            until = max(_S["until"], _disk_until())
            if until > now:
                key = (str(out), until)
                if out is not None and key not in _S["noticed"]:
                    _S["noticed"].add(key)
                    try:
                        event(out, "youtube_paused", seconds=round(until - now, 1))
                    except OSError:
                        pass
                delay = until - now
            elif not take:
                return
            elif _S["active"] >= CONCURRENCY:
                delay = 1.0
            else:
                delay = _take()
                if delay <= 0:
                    _S["active"] += 1
                    return
            if time.monotonic() - started > MAX_WAIT_SECONDS:
                raise YouTubeBlocked("YouTube gate closed for %.0f s" % (time.monotonic() - started))
            cond.wait(min(max(delay, 0.05), 5.0))
            if out is not None:
                cond.release()
                try:
                    check_cancelled(out)
                finally:
                    cond.acquire()


@contextlib.contextmanager
def _file_lock(path):
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT)
    try:
        if os.name == "nt":
            import msvcrt
            for _ in range(300):
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.01)
            else:
                raise OSError("bucket lock busy")
            try:
                yield
            finally:
                os.lseek(fd, 0, 0)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _take():
    """One token from the bucket every process shares; 0 when taken, else the wait.

    A cache folder that cannot be written falls back to this process's own
    bucket rather than stopping YouTube.
    """
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / "bucket.json"
        with _file_lock(CACHE_DIR / "bucket.lock"):
            try:
                d = json.loads(path.read_text(encoding="utf-8"))
                tokens, stamp = float(d["tokens"]), float(d["stamp"])
            except (OSError, ValueError, KeyError, TypeError):
                tokens, stamp = float(BURST), time.time()
            now = time.time()
            tokens = min(float(BURST), tokens + max(0.0, now - stamp) * RPM / 60.0)
            taken = tokens >= 1.0
            path.write_text(json.dumps({"tokens": tokens - taken, "stamp": now}), encoding="utf-8")
    except OSError:
        mono = time.monotonic()
        _S["tokens"] = tokens = min(float(BURST), _S["tokens"] + (mono - _S["stamp"]) * RPM / 60.0)
        _S["stamp"] = mono
        taken = tokens >= 1.0
        _S["tokens"] -= taken
    return 0.0 if taken else (1.0 - tokens) * 60.0 / RPM


def _release():
    with _S["cond"]:
        _S["active"] = max(0, _S["active"] - 1)
        _S["cond"].notify_all()


def report(exc, kind, out=None, began=None):
    """Pause every YouTube call after a refusal; returns the pause in seconds.

    Refusals of calls that were already running when the pause began are
    the same incident and do not lengthen it.
    """
    out = _film(out)
    began = time.time() if began is None else began
    with _S["cond"]:
        if began < _S["paused_at"]:
            return 0.0
        _S["streak"] += 1
        seconds = min(BACKOFF_MAX_SECONDS, BACKOFF_SECONDS * 2 ** (_S["streak"] - 1))
        now = time.time()
        _S["paused_at"] = now
        _S["until"] = max(_S["until"], now + seconds)
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            tmp = _pause_file().with_suffix(".tmp%d" % threading.get_ident())
            tmp.write_text(json.dumps({"until": _S["until"], "streak": _S["streak"], "pid": os.getpid(),
                                       "error": str(exc)[:200]}), encoding="utf-8")
            os.replace(tmp, _pause_file())
        except OSError:
            pass
        _S["cond"].notify_all()
        streak = _S["streak"]
    if out is not None:
        try:
            event(out, "youtube_backoff", kind=kind, seconds=seconds, streak=streak, error=str(exc)[:200])
        except OSError:
            pass
    return seconds


def call(kind, fn, out=None):
    """fn() under the gate; kind names the request in the counts and events."""
    for attempt in range(1 + BLOCK_RETRIES):
        _wait(out, take=True)
        began = time.time()
        with _S["cond"]:
            _S["calls"][kind] = _S["calls"].get(kind, 0) + 1
        try:
            result = fn()
        except Exception as exc:
            _release()
            if throttled(exc):
                report(exc, kind, out, began)
                if attempt < BLOCK_RETRIES:
                    continue
            raise
        _release()
        with _S["cond"]:
            if began >= _S["paused_at"]:
                _S["streak"] = 0
        return result


def counts():
    """The calls made through the gate in this process, by kind."""
    with _S["cond"]:
        return dict(_S["calls"])
