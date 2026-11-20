"""What YouTube already answered, kept for every film on this machine.

The four parallel films of 2026-10-27 asked YouTube again for what one of
them, or their own earlier round, had just been told: an expansion round
searched its previous queries again in new folders (31 of ~100 searches
per film), probed the sources it already held again, and every window
download extracted the video's page once more although the probe had
read it seconds before. A rerun of the same film asked for everything
again.

Kept here, under %LOCALAPPDATA%\\documentary_materials\\yt_cache:

- json/<kind>/: search results and probe metadata, with a time to live;
- info/: the probe's full extraction (format URLs), as long as YouTube's
  own "expire" on those URLs allows, so a download needs no second
  extraction;
- windows/ and full/: downloaded windows by (video id, start, end,
  height) and whole files by (video id, height). A film takes a cached
  file as a hard link in its own sources folder (a copy when the link is
  not possible), so its paths, sidecars and markers stay its own, and
  deleting a film's folder removes only its link. The shared files are
  capped at DOCUMENTARY_YT_CACHE_GB and the least recently used go first;
- storyboard/: the storyboard sheets of a video.

Nothing here decides anything: a miss is the request that was made before.
"""
import gzip
import hashlib
import json
import os
import shutil
import threading
import time
import urllib.parse
from pathlib import Path

from . import yt_gate

SEARCH_TTL = float(os.environ.get("DOCUMENTARY_YT_SEARCH_TTL_HOURS", "72")) * 3600
PROBE_TTL = float(os.environ.get("DOCUMENTARY_YT_PROBE_TTL_HOURS", "12")) * 3600
STORYBOARD_TTL = 30 * 86400
# Format URLs carry their own "expire"; the info is dropped this long
# before it, and kept at most INFO_TTL when a URL has none.
INFO_MARGIN = 20 * 60
INFO_TTL = 3 * 3600
CAP_BYTES = float(os.environ.get("DOCUMENTARY_YT_CACHE_GB", "20")) * (1 << 30)

def _root():
    return yt_gate.CACHE_DIR


_S = globals().get("_S")
if _S is None:
    _S = {"lock": threading.Lock(), "puts": 0, "evicted_at": 0.0}


def _key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:32]


def _write(path, data, gz=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp%d" % threading.get_ident())
    blob = json.dumps(data, ensure_ascii=False).encode("utf-8")
    tmp.write_bytes(gzip.compress(blob, 5) if gz else blob)
    os.replace(tmp, path)


def _read(path, gz=False):
    try:
        blob = path.read_bytes()
        return json.loads(gzip.decompress(blob) if gz else blob)
    except (OSError, ValueError, EOFError):
        return None


def get_json(kind, key, ttl):
    """The value stored under (kind, key) when younger than ttl seconds, else None."""
    found = _read(_root() / "json" / kind / (_key(key) + ".json"))
    if not found or found.get("key") != key or time.time() - float(found.get("saved") or 0) > ttl:
        return None
    return found.get("value")


def put_json(kind, key, value):
    try:
        _write(_root() / "json" / kind / (_key(key) + ".json"),
               {"key": key, "saved": time.time(), "value": value})
    except OSError:
        pass
    _prune_sometimes()


# ---------------------------------------------------------------------------
# The full extraction of a video
# ---------------------------------------------------------------------------

def _info_path(video_id):
    return _root() / "info" / (_key(["info", video_id]) + ".json.gz")


def _expires(info):
    stamps = []
    for f in info.get("formats") or []:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(str(f.get("url") or "")).query)
        if q.get("expire"):
            try:
                stamps.append(float(q["expire"][0]))
            except ValueError:
                pass
    now = time.time()
    return min(min(stamps) - INFO_MARGIN, now + INFO_TTL * 2) if stamps else now + INFO_TTL


def get_info(video_id):
    if not video_id:
        return None
    found = _read(_info_path(video_id), gz=True)
    if not found or found.get("id") != video_id or time.time() >= float(found.get("valid_until") or 0):
        return None
    return found.get("info")


def put_info(video_id, info):
    if not video_id or not info:
        return
    try:
        _write(_info_path(video_id), {"id": video_id, "valid_until": _expires(info), "info": info}, gz=True)
    except (OSError, TypeError, ValueError):
        pass


def drop_info(video_id):
    try:
        _info_path(video_id).unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Downloaded media
# ---------------------------------------------------------------------------

def _safe(name):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(name))


def window_entry(video_id, start, end, height):
    return _root() / "windows" / _safe(video_id) / ("%.3f_%.3f_%s.mp4" % (float(start), float(end), _safe(height)))


def full_entry(video_id, height, ext="mp4"):
    return _root() / "full" / ("%s_%s.%s" % (_safe(video_id), _safe(height), ext))


def _touch(entry):
    # The use time lives beside the file: touching the file itself would
    # change the mtime of every film's hard link and void their scan caches.
    try:
        Path(str(entry) + ".used").write_bytes(b"")
    except OSError:
        pass


def take(entry, target):
    """Put a cached file at target (hard link, else copy); True when it was there."""
    entry, target = Path(entry), Path(target)
    try:
        if not entry.is_file() or entry.stat().st_size == 0:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()
        try:
            os.link(entry, target)
        except OSError:
            shutil.copy2(entry, target)
    except OSError:
        return False
    _touch(entry)
    return True


def store(source, entry):
    """Keep a downloaded file in the shared cache; returns the entry or None."""
    source, entry = Path(source), Path(entry)
    try:
        if not source.is_file() or source.stat().st_size == 0:
            return None
        entry.parent.mkdir(parents=True, exist_ok=True)
        if not entry.exists():
            tmp = entry.with_name(entry.name + ".tmp%d" % threading.get_ident())
            try:
                os.link(source, tmp)
            except OSError:
                shutil.copy2(source, tmp)
            os.replace(tmp, entry)
    except OSError:
        return None
    _touch(entry)
    evict()
    return entry


def same_file(a, b):
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def _media():
    for folder in ("windows", "full"):
        root = _root() / folder
        if root.is_dir():
            for path in root.rglob("*"):
                if path.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov", ".m4v") and path.is_file():
                    yield path


def evict(cap=None, force=False):
    """Drop the least recently used media until the cache fits under cap bytes."""
    cap = CAP_BYTES if cap is None else cap
    with _S["lock"]:
        if not force and time.monotonic() - _S["evicted_at"] < 30:
            return 0
        _S["evicted_at"] = time.monotonic()
    rows = []
    for path in _media():
        try:
            used = Path(str(path) + ".used")
            stamp = used.stat().st_mtime if used.exists() else path.stat().st_mtime
            rows.append((stamp, path.stat().st_size, path))
        except OSError:
            continue
    total = sum(r[1] for r in rows)
    removed = 0
    for _stamp, size, path in sorted(rows):
        if total <= cap:
            break
        try:
            # A film that took the file holds its own link, so its copy
            # stays; a file another process has open is left for later.
            path.unlink()
        except OSError:
            continue
        for extra in (".used", ".index.json"):
            try:
                Path(str(path) + extra).unlink()
            except OSError:
                pass
        total -= size
        removed += 1
    return removed


def _prune_sometimes():
    """Every 200 writes, drop json and info entries past any use."""
    with _S["lock"]:
        _S["puts"] += 1
        if _S["puts"] % 200:
            return
    now = time.time()
    limit = max(SEARCH_TTL, PROBE_TTL)
    for path in (_root() / "json").rglob("*.json") if (_root() / "json").is_dir() else ():
        try:
            if now - path.stat().st_mtime > limit:
                path.unlink()
        except OSError:
            pass
    for path in (_root() / "info").glob("*.json.gz") if (_root() / "info").is_dir() else ():
        try:
            if now - path.stat().st_mtime > INFO_TTL * 2:
                path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Storyboard sheets
# ---------------------------------------------------------------------------

def storyboard_sheet(video_id, index):
    return _root() / "storyboard" / _safe(video_id) / ("%03d.jpg" % index)


def get_sheet(video_id, index):
    path = storyboard_sheet(video_id, index)
    try:
        if time.time() - path.stat().st_mtime <= STORYBOARD_TTL:
            return path.read_bytes()
    except OSError:
        pass
    return None


def put_sheet(video_id, index, blob):
    path = storyboard_sheet(video_id, index)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp%d" % threading.get_ident())
        tmp.write_bytes(blob)
        os.replace(tmp, path)
    except OSError:
        pass
