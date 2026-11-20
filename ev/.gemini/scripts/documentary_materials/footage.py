"""Which uploads carry the same footage.

The source rules count a recording by its origin, and the origin is a
YouTube id. One recording is uploaded again and again under other ids:
the livestream of the Key Bridge collapse reached the catalog through
at least four channels, and the finished film showed the same collapse
many times while every upload stayed under its own cap.

So the windows are compared by their pictures. Frames are sampled from
every video window and hashed; two uploads are the same footage when
most frames of a window of one have a near identical frame in a window
of the other. The answer is written to <out>/footage_groups.json and
handed to reservations, which counts one footage as one source. It is
not written into the catalog, because the catalog is part of every
shot's identity and a new field there would produce a finished film
again.
"""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import resources, scan_cache
from .io import event, save
from .reservations import origin_id, use_footage_groups
from .sources import local_time, shared_window

# A frame every two seconds, at least four and at most sixteen for a
# window. The windows are mostly 32 seconds; a frame every two seconds
# keeps the nearest frame of another upload within a second of it.
_FRAME_STEP = 2.0
_MIN_FRAMES, _MAX_FRAMES = 4, 16

# The picture is read small: the hash looks at the 16x16 lowest
# frequencies of a 64x64 image, and the letterbox is found on this size.
_W, _H = 128, 72

# The hash has 256 bits. The common 64 bit pHash (8x8 frequencies) was
# measured first and is too coarse here: an inclinometer on a dashboard
# and the anchor deck of a carrier came out 12 bits apart, closer than
# the same livestream frame in two uploads (up to 0.2 of the bits).
_SIDE, _LOW = 64, 16
_BITS = _LOW * _LOW
# The cache key carries the hash version, so hashes of another layout
# are not compared with these.
_VERSION = "phash256"

# Two frames are the same picture at this Hamming distance or less.
# Calibrated on the Key Bridge film: the livestream frames of two
# uploads lie at 0-60 bits (a news banner over it near 60), two aerials
# of the wreck by the same helicopter at 56-80, and unrelated footage
# at 90 and more. The groups are the same at 56 and at 64; the first
# wrong group (the two helicopter aerials) forms at 72.
FRAME_DISTANCE = 56

# A window pair is the same footage when this share of the frames of
# one window, and at least this many frames, have a match in the
# other, and the other window is mostly that footage as well. A news
# report or a documentary that quotes a few seconds of a clip matches
# a few of its frames, and the whole report is not the clip.
MATCH_SHARE = 0.6
OTHER_SHARE = 0.4
MIN_MATCHED_FRAMES = 4

# A frame with almost no structure (black, a fade, a flat sky) has a
# hash that is noise, and noise matches anything.
_MIN_CONTRAST = 6.0

_WORKERS = 12


def _hashes(gray):
    """The perceptual hash of the whole picture and of its centre.

    The letterbox and pillarbox bars are cut first, so a 4:3 upload
    inside a 16:9 frame hashes like the 4:3 original. The centre crop
    answers an upload that was cropped or zoomed: its whole picture is
    close to the centre of the original.
    """
    import cv2
    import numpy as np
    rows = np.where(gray.max(axis=1) > 24)[0]
    cols = np.where(gray.max(axis=0) > 24)[0]
    if len(rows) < _H * 0.4 or len(cols) < _W * 0.4:
        return None
    gray = gray[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1].astype(np.float32)
    h, w = gray.shape
    centre = gray[int(h * .1):int(h * .9), int(w * .1):int(w * .9)]
    out = []
    for view in (gray, centre):
        small = cv2.resize(view, (_SIDE, _SIDE), interpolation=cv2.INTER_AREA)
        if small.std() < _MIN_CONTRAST:
            return None
        low = cv2.dct(small)[:_LOW, :_LOW].flatten()
        bits = low > np.median(low[1:])
        out.append(int.from_bytes(np.packbits(bits).tobytes(), "big"))
    return out


def _measure(path, start, end):
    """The hashes of the sampled frames of one window, [] when unreadable.

    The window is decoded in full and sampled every two seconds. Reading
    only the keyframes was four times faster, but the downloaded windows
    carry a keyframe every four to six seconds, and on the Key Bridge
    film that sampling found 4 of the 10 uploads of the livestream.
    """
    import numpy as np
    span = end - start
    count = int(min(_MAX_FRAMES, max(_MIN_FRAMES, span // _FRAME_STEP)))
    try:
        proc = resources.probe_run(
            ["ffmpeg", "-hide_banner", "-nostats", "-v", "error",
             "-ss", str(local_time(path, start)), "-t", str(span), "-i", str(path),
             "-vf", "fps=%.6f,scale=%d:%d" % (count / span, _W, _H),
             "-frames:v", str(count), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
            timeout=120, cuda="exact")
    except Exception:
        return []
    frames = np.frombuffer(proc.stdout or b"", np.uint8)
    frames = frames[:len(frames) // (_W * _H) * _W * _H].reshape(-1, _H, _W)
    return [h for h in map(_hashes, frames) if h]


def fingerprint(asset):
    """The frame hashes of a video window, measured once per file and range."""
    path = asset.get("path")
    start, end = float(asset.get("start", 0)), float(asset.get("end", 0))
    if not path or end - start < 1 or not Path(path).is_file():
        return []
    # A window from the shared YouTube cache is keyed by the shared file,
    # so every film that takes it reads the same fingerprint.
    key = (str(shared_window(path) or path), round(start, 2), round(end, 2), _VERSION)
    single = getattr(scan_cache, "single_footage", None)
    # A bridge that was started before scan_cache had the footage store
    # does not reload scan_cache, so it measures without the cache until
    # it is restarted.
    if single is None:
        return _measure(path, start, end)
    return single(key, lambda: _measure(path, start, end))


# The windows are fingerprinted in the background while the run is
# still sourcing, so the grouping at the start of the shot production
# finds the cache warm. Measured on the Gotthard film, that grouping
# took 319 s cold, and 109 s again after the sentence search added its
# windows. The background pool is narrower than the grouping's own,
# because it shares the machine with the downloads.
_PREFETCH_WORKERS = 2
_prefetch_pool = None
_prefetch_lock = threading.Lock()


def prefetch(rows):
    """Start fingerprinting fetched video windows; returns at once.

    The rows are the raw windows as they land on disk; the catalog
    keeps their path and range, so the cache key is the one the
    grouping asks for. A window that is later rejected costs a few
    seconds of a background thread and nothing else.
    """
    global _prefetch_pool
    rows = [r for r in rows or [] if r.get("kind") == "VIDEO"]
    if not rows:
        return
    with _prefetch_lock:
        if _prefetch_pool is None:
            _prefetch_pool = ThreadPoolExecutor(max_workers=_PREFETCH_WORKERS,
                                                thread_name_prefix="footage-prefetch")
    for row in rows:
        _prefetch_pool.submit(_fingerprint_beside_the_run, row)


def _fingerprint_beside_the_run(row):
    """fingerprint(row), started only while a heavy media job still fits beside it.

    The gate admits a light job whenever the light job fits, so a queue
    of background fingerprints held the budget of a busy machine and
    the run's own heavy jobs, the window probes of the sourcing and the
    frame samples of the classification, waited for it: 12 s per window
    probe instead of 0.07 s, with 1.6 GB free.
    """
    while not resources.MEDIA.has_room(resources.MEDIA.per_unit_mb + resources.LIGHT_MB):
        time.sleep(1)
    return fingerprint(row)


def _bits(values):
    import numpy as np
    raw = np.frombuffer(b"".join(v.to_bytes(_BITS // 8, "big") for v in values), np.uint8)
    return np.unpackbits(raw.reshape(-1, _BITS // 8), axis=1).astype(np.float32) * 2 - 1


def match_counts(windows):
    """For every window pair, how many frames of the first match the second.

    windows is a list of hash lists. The distance of two frames is the
    smallest of whole-to-whole, centre-to-centre and the two mixed
    pairs, so a crop of either upload still finds its frame.
    """
    import numpy as np
    sizes = [len(w) for w in windows]
    n = len(windows)
    counts = np.zeros((n, n), dtype=np.int32)
    if not sum(sizes):
        return counts
    flat = [h for w in windows for h in w]
    full, centre = _bits([h[0] for h in flat]), _bits([h[1] for h in flat])
    owner = np.repeat(np.arange(n), sizes)
    starts = np.cumsum([0] + sizes[:-1])
    nonempty = np.array(sizes) > 0
    for lo in range(0, len(flat), 512):
        a_full, a_centre = full[lo:lo + 512], centre[lo:lo + 512]
        # Hamming distance of +-1 vectors: (bits - dot) / 2.
        best = (_BITS - np.maximum.reduce([a_full @ full.T, a_centre @ centre.T,
                                           a_full @ centre.T, a_centre @ full.T])) / 2
        nearest = np.full((len(best), n), float(_BITS), dtype=np.float32)
        nearest[:, nonempty] = np.minimum.reduceat(best, starts[nonempty], axis=1)
        np.add.at(counts, owner[lo:lo + 512], (nearest <= FRAME_DISTANCE).astype(np.int32))
    return counts


def same_footage_pairs(windows):
    """The window index pairs that show the same footage.

    Most frames of one window have to match, and a good part of the
    other one too. A still window (a bridge at night, a parked ship)
    would otherwise match a window that shows the same kind of picture
    for one second: all its frames find that one frame.
    """
    import numpy as np
    counts = match_counts(windows)
    sizes = np.array([max(1, len(w)) for w in windows])
    share = counts / sizes[:, None]
    ok = ((share >= MATCH_SHARE) & (share.T >= OTHER_SHARE)
          & (counts >= MIN_MATCHED_FRAMES) & (counts.T >= MIN_MATCHED_FRAMES))
    ok = ok | ok.T
    return [(i, j) for i, j in zip(*np.nonzero(np.triu(ok, 1)))]


def group_origins(assets):
    """{origin: group} for the uploads that share footage with another upload.

    Only VIDEO windows are compared; two windows of one upload are one
    origin already. The group is named after its smallest member, so
    the same members always give the same name.
    """
    seen, windows = set(), []
    for a in assets:
        key = (a.get("path"), a.get("start"), a.get("end"))
        if a.get("category") == "VIDEO" and key not in seen:
            seen.add(key)
            windows.append(a)
    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        prints = list(pool.map(fingerprint, windows))
    origins = [origin_id(a) for a in windows]
    parent = {o: o for o in origins}

    def root(o):
        while parent[o] != o:
            parent[o] = parent[parent[o]]
            o = parent[o]
        return o

    for i, j in same_footage_pairs(prints):
        if origins[i] != origins[j]:
            parent[root(origins[i])] = root(origins[j])
    members = {}
    for o in parent:
        members.setdefault(root(o), set()).add(o)
    return {o: "footage:" + min(group) for group in members.values() if len(group) > 1 for o in group}


def refresh(out, assets):
    """Group the catalog and the supplemental windows, save and apply the answer.

    The supplemental manifests are read from the run folder, so a call
    after a recovery search sees the windows it added.
    """
    out = Path(out)
    extra = []
    for manifest in sorted((out / "sources" / "supplemental").glob("*.json")):
        try:
            extra += json.loads(manifest.read_text(encoding="utf-8")).get("assets") or []
        except (OSError, ValueError):
            continue
    started = time.perf_counter()
    try:
        groups = group_origins(list(assets) + extra)
    except Exception as exc:
        # Without the groups every upload is its own source, which is
        # how the film was made before; the run goes on, and says so.
        event(out, "footage_groups_failed", detail=str(exc)[-300:])
        return load(out)
    save(out / "footage_groups.json", {"groups": groups})
    use_footage_groups(groups)
    event(out, "footage_groups", groups=len(set(groups.values())), origins=len(groups),
          seconds=round(time.perf_counter() - started, 1))
    return groups


def load(out):
    """Apply the groups saved for a run folder, when it has them."""
    try:
        groups = json.loads((Path(out) / "footage_groups.json").read_text(encoding="utf-8"))["groups"]
    except (OSError, ValueError, KeyError):
        return {}
    use_footage_groups(groups)
    return groups
