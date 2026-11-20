"""Per-range side-bar / pillarbox / portrait detector for stage 3 (runs BEFORE the render).

Measured on EP02+EP03 1107 (testbench/darbogaz_1107/V_rangebars/RESULT.md): it finds 43 of the 47 candidates
Flash refused for side bars or portrait video, and flags 0 of 117 passed ones. A flagged candidate is refused
without a Flash call and its window goes to the film-wide geometry memory (runner._prerender_precheck).

    range_has_side_bars(path, start, end) -> (bool, score)

path/start/end are the file and the seconds INSIDE that file (for yt window files: source_second - window.source_start,
see sources.py local-time mapping). score = width share (0..0.5) of the narrower bar, 1.0 for a portrait/square-ish file.

Rule (chosen on EP02/EP03 data, see RESULT.md):
  1. file aspect w/h < 1.2 (720x960, 9:16 ...)            -> True  (4:3 files are NOT flagged: Flash passes them)
  2. else 3 gray 320x180 frames at keyframes inside [start,end]; per column the MEDIAN over rows of |dI/dy| < 1.0 means
     "flat/black column"; bar width = run of flat columns from each edge; median over the frames.
     bars iff BOTH sides >= 3% of the width and L+R < 0.9 (not an all-black/slide frame).
Cost ~0.4 CPU-s (1 ffprobe packet listing cached per file + 1 ffmpeg, -threads 1, keyframes only).
"""
import subprocess, functools
import numpy as np

W, H = 320, 180
POS = (0.15, 0.5, 0.85)
FFMPEG, FFPROBE = "ffmpeg", "ffprobe"
NO_WINDOW = 0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
ASPECT_MAX = 1.2
FLAT_T = 1.0
MIN_SHARE = 0.03
MAX_BOTH = 0.9


@functools.lru_cache(maxsize=1024)
def _dims(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, creationflags=NO_WINDOW)
    try:
        w, h = (int(x) for x in r.stdout.split()[0].split(",")[:2])
        return w, h
    except Exception:
        return 0, 0


@functools.lru_cache(maxsize=1024)
def _keyframes(path):
    """Keyframe times (packet flags only, no decoding: ~0.05 CPU-s per file)."""
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,flags",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, creationflags=NO_WINDOW)
    ks = []
    for line in r.stdout.splitlines():
        p = line.split(",")
        if len(p) >= 2 and "K" in p[1]:
            try:
                ks.append(float(p[0]))
            except ValueError:
                pass
    return tuple(sorted(ks))


def _pick_times(path, start, end):
    """(times, keyonly): keyframes inside the range nearest to 15/50/85 %, else accurate seeks."""
    d = max(0.0, end - start)
    targets = [start + p * d for p in POS]
    ks = [k for k in _keyframes(path) if start - 0.02 <= k <= end]
    if ks:
        chosen = sorted({min(ks, key=lambda k: abs(k - t)) for t in targets})
        return chosen, True
    return [start + 0.35 * d, start + 0.7 * d], False   # no keyframe inside: 2 accurate seeks (decode from the previous GOP)


def _grab(path, times, keyonly):
    cmd = [FFMPEG, "-v", "error", "-threads", "1"]
    for t in times:
        if keyonly:
            cmd += ["-noaccurate_seek", "-skip_frame", "nokey"]
        cmd += ["-ss", f"{t + (0.01 if keyonly else 0):.3f}", "-i", str(path)]
    n = len(times)
    fc = "".join(f"[{i}:v]scale={W}:{H}:flags=fast_bilinear,format=gray[v{i}];" for i in range(n))
    fc += "".join(f"[v{i}]" for i in range(n)) + (f"vstack=inputs={n}[o]" if n > 1 else "null[o]")
    cmd += ["-filter_complex", fc, "-map", "[o]", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    r = subprocess.run(cmd, capture_output=True, creationflags=NO_WINDOW)
    a = np.frombuffer(r.stdout, np.uint8)
    return a.reshape(n, H, W) if a.size == n * W * H else None


def _edge_runs(img):
    f = img.astype(np.float32)
    col = np.median(np.abs(np.diff(f, axis=0)), axis=0)
    flat = col < FLAT_T
    n = len(flat)
    L = 0
    while L < len(flat) and flat[L]:
        L += 1
    R = 0
    while R < len(flat) and flat[len(flat) - 1 - R]:
        R += 1
    return L / n, R / n


def frames_have_side_bars(frames):
    runs = [_edge_runs(f) for f in frames]
    L = float(np.median([r[0] for r in runs]))
    R = float(np.median([r[1] for r in runs]))
    return (min(L, R) >= MIN_SHARE and L + R < MAX_BOTH), min(L, R)


def range_has_side_bars(path, start, end):
    """(has_side_bars, score). Never raises: any failure -> (False, 0.0) so a shot is never starved by the detector."""
    try:
        w, h = _dims(str(path))
        if w and h and w / h < ASPECT_MAX:
            return True, 1.0
        times, keyonly = _pick_times(str(path), float(start), float(end))
        fr = _grab(path, times, keyonly)
        if fr is None and keyonly:
            fr = _grab(path, [float(start) + 0.5 * (float(end) - float(start))], False)
        if fr is None:
            return False, 0.0
        return frames_have_side_bars(fr)
    except Exception:
        return False, 0.0
