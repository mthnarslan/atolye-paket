"""One decode of a fetched window answers every per-shot picture check.

Each shot used to read its own range of the window again for the scene
cuts, the motion score, the freeze filter and two face reads: five
ffmpeg processes per shot, which waited on the media gate. On TOPIC_2
they took 20-30 s of a shot's ~70 s. The window is decoded here once,
as soon as it lands, while the other sources still download, and the
shot checks read their range out of the index. A window without an
index (not built yet, or the build failed) is measured the old way, so
the index only ever saves time and never changes who decides.

The index is kept beside the window as <file>.index.json, so a resumed
run reads it instead of decoding again.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import threading

import numpy as np

from . import resources

# Bumped when what the index holds changes, so an old file is rebuilt.
VERSION = 1

# The face areas the callers ask about: the film's line, the default
# and the hook's. A second answers each of them.
FACE_AREAS = (0.02, 0.04, 0.08)

# The frame the face detector reads, as the per-shot read scaled it.
_FACE_SIZE = (640, 360)

_WORKERS = 3

# Longer files are not indexed (see build).
MAX_SECONDS = 600
_INDEX = {}
_lock = threading.Lock()
_pool = None


def _target(path):
    # A window taken from the shared YouTube cache (yt_cache) keeps its
    # index beside the shared file, so the next film that takes the same
    # window reads it instead of decoding again.
    from . import sources
    shared = sources.shared_window(path)
    return Path(str(shared or path) + ".index.json")


def get(path):
    """The index of a window file, or None when it is not built."""
    key = str(path)
    found = _INDEX.get(key)
    if found is not None:
        return found
    target = _target(path)
    if target.is_file():
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            if data.get("version") == VERSION and data.get("size") == Path(path).stat().st_size:
                _INDEX[key] = data
                return data
        except (OSError, ValueError):
            pass
    return None


def prefetch(rows):
    """Start indexing fetched video windows; returns at once."""
    global _pool
    paths = list(dict.fromkeys(r["path"] for r in rows or [] if r.get("kind") == "VIDEO" and r.get("path")))
    if not paths:
        return
    with _lock:
        if _pool is None:
            _pool = ThreadPoolExecutor(max_workers=_WORKERS, thread_name_prefix="window-index")
    for path in paths:
        _pool.submit(_build_quietly, path)


def _build_quietly(path):
    try:
        build(path)
    except Exception:
        pass  # the shot checks measure an unindexed window themselves


def build(path):
    """Decode the window once and keep what the shot checks ask for."""
    if get(path) is not None or not Path(path).is_file():
        return get(path)
    # A whole long source (a fetch that fell back to the full file) would
    # hold a decode slot for minutes; its shots read their own ranges.
    if _duration(path) > MAX_SECONDS:
        return None
    graph = ("[0:v]split=3[a][b][c];"
             "[a]freezedetect=n=0.003:d=3.0,nullsink;"
             "[b]scale=320:-1,select='gt(scene,0.3)',showinfo,nullsink;"
             "[c]scale=320:-1,tblend=all_mode=difference,signalstats,"
             "metadata=print:key=lavfi.signalstats.YAVG[m]")
    proc = resources.decode_run(["ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(path),
                                 "-filter_complex", graph, "-map", "[m]", "-an", "-f", "null", "-"],
                                timeout=180, text=True, cuda=True)
    log = proc.stderr or ""
    if proc.returncode != 0:
        return None
    cuts = [float(t) for t in re.findall(r"Parsed_showinfo\S*\s.*?pts_time:([\d.]+)", log)]
    starts = [float(t) for t in re.findall(r"freeze_start:\s*([\d.]+)", log)]
    ends = [float(t) for t in re.findall(r"freeze_end:\s*([\d.]+)", log)]
    duration = _duration(path)
    freezes = [[a, ends[i] if i < len(ends) else duration] for i, a in enumerate(starts)]
    motion = []
    stamp = None
    for line in log.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m and "Parsed_metadata" in line:
            stamp = float(m.group(1))
        m = re.search(r"YAVG=([\d.]+)", line)
        if m and stamp is not None:
            motion.append([stamp, float(m.group(1))])
    data = {"version": VERSION, "size": Path(path).stat().st_size, "duration": duration,
            "cuts": cuts, "freezes": freezes, "motion": motion, "faces": _faces(path)}
    _INDEX[str(path)] = data
    try:
        _target(path).write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass
    return data


def _duration(path):
    proc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                          capture_output=True, text=True, timeout=30)
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


def _faces(path):
    """For each second of the window, which face areas a person covers."""
    from .runner import _detect_talking_head, _detect_talking_head_safe
    if _detect_talking_head is None:
        return None
    w, h = _FACE_SIZE
    proc = resources.decode_run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(path),
                                 "-vf", f"fps=1,scale={w}:{h}", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"],
                                timeout=180, cuda=True)
    raw = proc.stdout or b""
    frames = np.frombuffer(raw, np.uint8)[: len(raw) // (w * h * 3) * (w * h * 3)].reshape(-1, h, w, 3)
    seconds = []
    for frame in frames:
        flags = [False] * len(FACE_AREAS)
        if _detect_talking_head_safe(frame, FACE_AREAS[0])[0]:
            flags = [bool(_detect_talking_head_safe(frame, area)[0]) for area in FACE_AREAS]
        seconds.append(flags)
    return seconds


def cuts(path, local_start, duration):
    """The local seconds of the picture cuts inside a range, or None."""
    data = get(path)
    if data is None:
        return None
    return [t for t in data["cuts"] if local_start < t <= local_start + duration]


def motion(path, local_start, duration):
    """The motion score of a range as _motion_score measures it, or None."""
    data = get(path)
    if data is None:
        return None
    values = [v for t, v in data["motion"] if local_start <= t <= local_start + duration]
    if not values:
        return {"mean": 0.0, "peak": 0.0, "frames": 0, "measured": False}
    return {"mean": sum(values) / len(values), "peak": max(values), "frames": len(values), "measured": True}


def freezes(path, local_start, duration):
    """The frozen seconds inside a range, each clipped to it, or None."""
    data = get(path)
    if data is None:
        return None
    end = local_start + duration
    return [min(b, end) - max(a, local_start) for a, b in data["freezes"]
            if min(b, end) - max(a, local_start) > 0]


def face(path, local_start, local_end, area):
    """True when a person covers area of the frame in some second of the range.

    None when the window has no index or the area is not one it holds;
    every second of the range is read, where a per-shot read sampled a few.
    """
    data = get(path)
    if data is None or data.get("faces") is None or area not in FACE_AREAS:
        return None
    column = FACE_AREAS.index(area)
    seconds = data["faces"]
    first, last = int(local_start), min(len(seconds) - 1, int(local_end))
    return any(seconds[s][column] for s in range(max(0, first), last + 1))
