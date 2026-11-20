"""The caches of the hook candidate scan, kept out of the reload path.

The bridge reloads the material modules before every stage request so a
code change takes effect without a restart, and a reload re-executes
the module it reloads. A cache that lives in a module level dict is
emptied by that, so the measurement of the first run is thrown away
and the second run pays for it again.

Measured on the live run: the hook scan of 4622 video candidates cost
1774 seconds of motion measurement, and the reload in front of the
next stage request emptied the cache, so the same 4622 candidates
were measured a second time for about 1583 seconds more. The work was
identical and the answer was identical, and the second run paid for
it again.

The motion cache and the talking head cache live here instead, and the
bridge does not reload this module: the caches are imported by name and
kept as module objects, so a reload of the material package leaves
them in place. The bridge makes the same exception for the registry of
active runs, for the same reason and with the same shape.

A cache that outlives a reload also outlives a change to the code that
filled it. The entries are keyed by the range they were measured on,
so a range that was measured once is not measured again; a change to
the measurement itself is not seen by a cache that is already warm.
"""
import json
import os
import threading
from pathlib import Path

_lock = threading.Lock()

# A bridge restart also emptied the caches, and every restart paid for
# the hook scan again (several minutes each). Each answer is appended to
# a file next to this module and read back at import, tagged with the
# size and mtime of the file it was measured on, so a window fetched
# again under the same name is measured again.
_DISK = Path(__file__).with_name(".scan_cache")


def _stamp(path):
    try:
        st = os.stat(path)
        return [st.st_size, st.st_mtime_ns]
    except OSError:
        return None


def _load(name):
    store = {}
    try:
        lines = (_DISK / (name + ".jsonl")).read_text(encoding="utf-8").splitlines()
    except OSError:
        return store
    for line in lines:
        try:
            key, stamp, value = json.loads(line)
        except ValueError:
            continue
        if stamp and _stamp(key[0]) == stamp:
            store[tuple(key)] = value
    return store


# The motion score of a source range, by (path, start, duration).
MOTION_CACHE = _load("motion")

# The talking head verdict of a source range, by (path, start, end).
TALKING_HEAD_CACHE = _load("talking_head")

# The frame hashes of a video window, by (path, start, end): footage.py
# compares them to find the uploads that carry the same footage.
FOOTAGE_CACHE = _load("footage")

_FILES = {id(MOTION_CACHE): "motion", id(TALKING_HEAD_CACHE): "talking_head",
          id(FOOTAGE_CACHE): "footage"}


def _persist(store, key, value):
    stamp = _stamp(key[0])
    if not stamp:
        return
    try:
        _DISK.mkdir(exist_ok=True)
        with open(_DISK / (_FILES[id(store)] + ".jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps([list(key), stamp, value]) + "\n")
    except (OSError, TypeError, ValueError):
        pass  # the in-memory cache still holds the answer

# The in flight guards, so two threads that ask for the same range at
# the same time measure it once instead of twice.
_motion_guards = {}

_talking_head_guards = {}

_footage_guards = {}

# How long a thread waits for the thread that is measuring the same
# range. It is longer than the longest measurement: the motion
# measurement gives up after 30 seconds and the frame read after 60.
_GUARD_WAIT = 180.0


def single_motion(key, measure):
    """The motion score of a range, measured once.

    The measure function returns the score and does not raise: the
    caller decides what a range it cannot read is worth.
    """
    return _single(MOTION_CACHE, _motion_guards, key, measure)


def single_talking_head(key, measure):
    """The talking head verdict of a range, read once.

    The measure function returns the verdict and does not raise.
    """
    return _single(TALKING_HEAD_CACHE, _talking_head_guards, key, measure)


def single_footage(key, measure):
    """The frame hashes of a window, read once."""
    return _single(FOOTAGE_CACHE, _footage_guards, key, measure)


def _single(store, guards, key, measure):
    """The value of a key, measured by the first thread that asks for it.

    A thread that arrives while the range is being measured waits for
    the answer instead of starting a second ffmpeg process for the
    same range.
    """
    with _lock:
        if key in store:
            return store[key]
        guard = guards.get(key)
        if guard is None:
            guard = threading.Event()
            guards[key] = guard
            owner = True
        else:
            owner = False
    if not owner:
        guard.wait(_GUARD_WAIT)
        with _lock:
            if key in store:
                return store[key]
        # The thread that had the range did not finish it. Measuring it
        # here is slower than waiting, but it is not wrong.
        return measure()
    try:
        value = measure()
    except BaseException:
        with _lock:
            guards.pop(key, None)
        guard.set()
        raise
    with _lock:
        store[key] = value
        guards.pop(key, None)
        _persist(store, key, value)
    guard.set()
    return value
