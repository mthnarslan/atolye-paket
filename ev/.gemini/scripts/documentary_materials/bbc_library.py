"""A local library of BBC natural-history episodes, searched by sentence.

The YouTube BBC channels gave TOPIC_2 16 usable sources for ~59 cuts, and
whole BBC series sit on archive.org in 1080p (the user has written
clearance for this use). archive.org serves them at about 1.5-11 MB/s,
so an hour-long episode takes minutes to fetch: far too slow inside a
film. The episodes are fetched once, in the background (`sync`), and
each is scanned once with the run's SigLIP2 model at one frame every two
seconds; a 60-minute episode scanned in 18 s. A film then ranks every
library second against its sentences in about a second (`search`) and
cuts the matching windows out of the local files (`cut_windows`), which
enter the catalog like fetched YouTube windows.

    python -m documentary_materials.bbc_library sync      # fetch + scan
    python -m documentary_materials.bbc_library status
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import zipfile
import urllib.parse

import numpy as np
import requests

LIBRARY = Path(os.environ.get("BBC_LIBRARY", "C:/Users/meteh/BBCLibrary"))

# archive.org items of BBC natural-history series published in 1920x1080,
# most broadly useful first (checked 2026-10-24 through the metadata API).
ITEMS = (
    "planet-earth-II-2016-bbc",
    "seven-worlds-one-planet-bbc",
    "FrozenPlanetIIBBC",
    "frozen-planet-BBC-2011",
    "planetearth2006_202301",
    "BluePlanetIIBBCTVminiseries",
    "planet-earth-III",
    "SpyInTheWildSeries1BBC",
    "SpyInTheWildSeries2BBC",
    "life-in-cold-blood-bbc",
    # Added 2026-10-25 after an archive.org survey: whole BBC natural-history
    # series in 1920x1080 mp4 that episodes() reads as they are.
    "Life2009TVminiseriesUSVersion", "vid-20230223-130530",
    "TheBluePlanetBBC", "thelifeofbirds1998BBC", "galapagos-2006-tv-miniseries",
    "big-cats-24-7-season-1", "big-cats-24-7-season-2", "south-pacific-bbc",
    "wild-australasia-2003-bbc", "wild-caribbean-2007-bbc", "SpyInTheOceanBBC",
    "PenguinsSpyintheHuddleBBC", "SharkBBC2015", "great-barrier-reef-2012-bbc",
    "NewZealand2016BBC", "mission-galapagos-bbc", "life-in-the-freezer-bbc",
    "LifeStoryBBC", "weird-nature-BBC", "planet-earth-a-celebration-2020-bbc",
    "penguins-meet-the-family-2020-bbc", "natures-biggest-beasts-BBC",
    "attenboroughs-big-birds-bbc-natural-world", "invasion-of-the-crocodiles-BBC",
    "buddha-bees-the-giant-hornet-queen-BBC", "giant-squid-filming-the-impossible-natural-world-BBC",
    "komodo-secrets-of-the-dragon-BBC", "HammerheadNaturalWorldBBC",
    "great-white-shark-a-living-legend-BBC", "PerfectSharkBBC",
    "snow-chick-a-penguins-tale-BBC", "IguanasLivingLikeDinosaursBBCWildlife",
    "grand-canyon-from-dinosaurs-to-dams-bbc-natural-world",
    "bbc-weasels-feisty-and-fearless-2019-1080p",
)

# Mixed archive.org collections: only the files whose name matches are BBC
# natural-history episodes worth scanning; mkv is taken here too (cut_windows
# re-encodes, so its keyframes do not matter). The Pantanal and South
# America titles (Jaguars - Brazil's Super Cats, Giant Otters of the Amazon,
# The Dark: Nature's Extraordinary Hunters / Amazon) are in these.
FILTERED_ITEMS = {
    "natural_world_collection": r"^Natural World .*\.(mp4|mkv)$",
    "bbc-documentary-fullhd-3": r"^BBC\.(The\.Dark\.Natures|Patagonia\.Earths|The\.Hunt\.|The\.Green\.Planet|Hidden\.Kingdoms|Galapagos|Serengeti|Spy\.in\.the\.Wild|Penguins|Mountain\.Life|Natures\.Epic|Natures\.Wonderlands|New\.Zealand\.Earths|Japan\.Earths|Thailand\.Earths|South\.Korea|India\.Natures|Hidden\.India|Great\.Bear|Great\.Barrier|Operation\.Iceberg|Snow\.C|Trek\.Spy|Worlds\.Sneakiest|Wales\.Land|Wild\.Shetland|Our\.Wild|Last\.Seabird|Islands\.and|Lake\.District)|^China\.Natures|^Oak\.Tree",
    "bbcdavidattenborough": r"^(BBC Africa E|BBC The Hunt \(2015\)|Nature's Great Events|Madagascar \(2011\))",
    "EarthflightEP1NordAmericaNorthAmerica1080pX624ItaEn": r"\.(mkv|mp4)$",
    "bbc-documentary-fullhd-2": r"^BBC\.(Dynasties|Attenboroughs\.Life\.in\.Colour|Attenboroughs\.Paradise|Attenboroughs\.Life\.That|Earth\.New\.Guinea|Earth\.from\.Space|Earth\.One\.Amazing|Earths\.Tropical|Earths\.Great\.Rivers|Cities\.Natures|Monkey\.Planet|Chris\.Packhams\.Animal|Australia\.Earths|Animal\.Babies|Bears\.About|Birds\.of\.Paradise|Life\.in\.Polar|Life\.in\.the\.Snow|Life\.in\.the\.Air|Mexico\.Earths|Natural\.World|Natures\.Turtle|Once\.Were\.Lions|A\.Wild\.Year)",
    "bbc-documentary-fullhd-4": r"^(Eden\.Untamed|PBS\.BBC\.Earth\.Life|BBC\.Natural\.World|BBC\.Serengeti|BBC\.Waterhole|BBC\.Spy\.in\.the\.Snow|BBC\.Wild\.Ireland|BBC\.Wonders\.of\.the\.Great|BBC\.Planet\.Ant|BBC\.The\.Secret\.Life\.of\.Rock|Born\.in\.China|BBC\.Snow\.Dogs|BBC\.Wild\.Tales)",
    "bbc-documentary-fullhd": r"^BBC\.(A\.Perfect\.Planet|Natural\.World|Animals\.with\.Cameras|Elephant\.Family|Lion\.The\.Rise|Super\.Small|Snow\.Animals|Into\.the\.Ice|Secret\.Life\.of\.Ice|A\.Day\.in\.the\.Life\.of\.Earth)|^24\.Hours\.On\.Earth",
}

STEP = 2.0          # seconds between scanned frames
_SIDE = 224         # the model's input side
WINDOW = 32.0       # the length of a window cut for the film, as a fetched one
MAX_PER_SENTENCE = 3
# A library second is a match when its fit, scored as picture_fit scores a
# candidate (sentence minus half the strongest title-card / presenter
# likeness), clears this line. picture_fit vetoes a pick below -0.01; the
# library offers only clear matches: on Frozen Lands the right Amur tiger
# seconds scored 0.13-0.15 and the wrong ones (a reindeer for a bear's
# blow, dark ice for deep powder) 0.10-0.12, so the line sits at 0.12 and
# the per-shot review judges the rest.
MIN_FIT = 0.12
# A sentence searched with its Flash expansions (three concrete
# descriptions of what a camera would see, expand()) is scored by the mean
# fit of the three. The mean sits lower than one sentence's fit, so it has
# its own line. On 30 TOPIC_1 sentences, top 3 each, judged blind by
# Flash: the raw sentence at 0.12 kept 82 moments, 19 PASS / 20 FAIL, 11
# sentences with a PASS; the expansions at 0.10 kept 73, 24 PASS / 19
# FAIL, 13 sentences with a PASS.
EXPANDED_MIN_FIT = 0.10

SCAN_FIRST = r"jaguar|otter|amazon|south america|sud america|brazil|pantanal|caiman|crocodil|the\.dark|flood|wetland|fresh ?water|jungle|rainforest|anaconda|capybara"

STALL_SECONDS = 300

# The old full downloads are deleted once their episode is scanned.
DELETE_LOCAL = True


def _log(message):
    LIBRARY.mkdir(parents=True, exist_ok=True)
    with open(LIBRARY / "sync.log", "a", encoding="utf-8") as handle:
        handle.write(time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n")


def episodes(item):
    """The 1080p episode files of an item: one per episode, original before the .ia copy.

    A FILTERED_ITEMS collection keeps only the files its pattern names, and
    takes mkv as well as mp4; a file without a width in the metadata counts
    as 1080p when its name says so.
    """
    meta = requests.get("https://archive.org/metadata/" + item, timeout=60).json()
    title = (meta.get("metadata") or {}).get("title") or item
    pattern = FILTERED_ITEMS.get(item)
    kinds = (".mp4", ".mkv") if pattern else (".mp4",)

    def hd(f):
        width = str(f.get("width") or "")
        return width == "1920" or (not width and "1080" in f["name"])

    files = [f for f in meta.get("files") or []
             if str(f.get("name", "")).lower().endswith(kinds) and hd(f) and int(f.get("size") or 0) > 100e6
             and (not pattern or re.search(pattern, f["name"].split("/")[-1]))]
    chosen = {}
    for f in sorted(files, key=lambda f: f["name"].endswith(".ia.mp4")):
        stem = f["name"][:-len(".ia.mp4")] if f["name"].endswith(".ia.mp4") else f["name"].rsplit(".", 1)[0]
        chosen.setdefault(stem, f)
    return [{"item": item, "title": title, "name": f["name"], "size": int(f["size"]),
             "url": "https://archive.org/download/%s/%s" % (item, urllib.parse.quote(f["name"])),
             "path": str(LIBRARY / item / f["name"])} for f in chosen.values()]


def _download(url, target, size):
    """Fetch url to target, resuming a partial file; True when complete."""
    target = Path(target)
    if target.is_file() and target.stat().st_size == size:
        return True
    part = target.with_suffix(target.suffix + ".part")
    part.parent.mkdir(parents=True, exist_ok=True)
    have = part.stat().st_size if part.is_file() else 0
    headers = {"Range": "bytes=%d-" % have} if have else {}
    with requests.get(url, headers=headers, stream=True, timeout=60) as response:
        if response.status_code not in (200, 206):
            return False
        mode = "ab" if response.status_code == 206 else "wb"
        with open(part, mode) as handle:
            for chunk in response.iter_content(8 << 20):
                handle.write(chunk)
    if part.stat().st_size != size:
        return False
    part.replace(target)
    return True


def _scan_path(path):
    return Path(str(path) + ".siglip.npz")


def _remote(path):
    """The archive.org download URL of a library episode path (LIBRARY/<item>/<file>)."""
    rel = Path(path).relative_to(LIBRARY)
    # A collection may keep its files in subfolders: <item>/<folder>/<file>.
    return "https://archive.org/download/%s/%s" % (rel.parts[0], urllib.parse.quote("/".join(rel.parts[1:])))


def _source(path):
    """Where an episode is read from: the local file if it is still here, else archive.org."""
    return str(path) if Path(path).is_file() else _remote(path)


# ffmpeg input options for an archive.org URL: a dropped connection is
# reopened where it stopped instead of ending the read.
_HTTP = ["-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "30", "-rw_timeout", "60000000"]


def _input(source):
    return (_HTTP if str(source).startswith("http") else []) + ["-i", str(source)]


def scan(path, source=None):
    """Embed one frame every STEP seconds of an episode; saved as <path>.siglip.npz.

    source is what ffmpeg reads (default: the local file or archive.org);
    the episode itself is never written to disk.
    """
    target = _scan_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        return target
    from . import picture_fit as pf
    import torch
    if pf._model() is None:
        raise RuntimeError("SigLIP model unavailable")
    model, _, _, device = pf._STATE["model"]
    size = _SIDE * _SIDE * 3
    proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-v", "error", "-nostats", "-skip_loop_filter", "all",
                             *_input(source or _source(path)), "-an", "-vf", f"fps=1/{STEP},scale={_SIDE}:{_SIDE}:flags=bicubic",
                             "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=size * 64,
                            # A film being made shares the machine: the scan yields.
                            creationflags=getattr(subprocess, "IDLE_PRIORITY_CLASS", 0))
    batches = queue.Queue(maxsize=4)

    def reader():
        while True:
            buf = proc.stdout.read(size * 64)
            if not buf:
                break
            batches.put(np.frombuffer(buf[: len(buf) // size * size], np.uint8).reshape(-1, _SIDE, _SIDE, 3))
        batches.put(None)

    threading.Thread(target=reader, daemon=True).start()
    vectors, dark = [], []
    with torch.no_grad():
        while True:
            # An archive.org read can stall for hours without failing (one
            # episode took 21,732 s on 2026-10-25): no frame for STALL_SECONDS
            # kills the read, and sync retries the episode.
            try:
                frames = batches.get(timeout=STALL_SECONDS)
            except queue.Empty:
                proc.kill()
                raise RuntimeError("stream stalled for %d s" % STALL_SECONDS)
            if frames is None:
                break
            dark.append(frames.mean((1, 2, 3)) < 20)
            x = torch.from_numpy(frames.copy()).to(device).permute(0, 3, 1, 2)
            x = x.half() if device == "cuda" else x.float()
            x = x.div(255).sub(0.5).div(0.5)
            with pf._STATE["run"]:
                vectors.append(pf._unit(model.encode_image(x).float()).cpu().numpy().astype(np.float16))
    proc.wait()
    if not vectors:
        raise RuntimeError("no frames decoded")
    emb = np.concatenate(vectors)
    # Written whole or not at all: a scan cut off mid-write left a 120 KB
    # "(04) Fish" file that np.load could not open (2026-10-27 04:11).
    part = target.with_name(target.name + ".part%d" % os.getpid())
    with open(part, "wb") as handle:
        np.savez(handle, emb=emb, dark=np.concatenate(dark), step=STEP)
    os.replace(part, target)
    return target


def _cpu_busy(limit=70):
    try:
        import psutil
        return psutil.cpu_percent(interval=2) > limit
    except Exception:
        return False


def _gpu_room(mb=2000):
    try:
        import torch
        return not torch.cuda.is_available() or torch.cuda.mem_get_info()[0] / 2**20 >= mb
    except Exception:
        return True


def sync(items=ITEMS + tuple(FILTERED_ITEMS), parallel=5):
    """Scan every episode of the library straight from archive.org; safe to rerun.

    Only the scan index (~2.6 MB an episode) is kept: ffmpeg reads the
    episode over HTTP, so a 1 TB library costs a few hundred MB of disk.
    An episode still on disk from the old full downloads is scanned from
    the file and the file is then deleted (DELETE_LOCAL).
    """
    try:
        import ctypes  # keep Windows from idle-sleeping while the scan runs
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    except Exception:
        pass
    todo = [e for item in items for e in _try(episodes, item) or []]
    # Wetland, South America and big-predator titles first: the films being
    # made now (TOPIC_1 Pantanal) need them most.
    todo.sort(key=lambda e: not re.search(SCAN_FIRST, e["name"], re.I))
    _log("sync: %d episodes in %d items (index only)" % (len(todo), len(items)))

    def one(e):
        if not _scan_path(e["path"]).is_file():
            # A film run holds the GPU (Sopro, SigLIP) and the CPU (window
            # checks); a new episode waits until both have room.
            while not _gpu_room() or _cpu_busy():
                time.sleep(30)
            for attempt in range(3):
                try:
                    started = time.time()
                    scan(e["path"])
                    _log("scanned %s/%s in %.0f s (%s)" % (e["item"], e["name"], time.time() - started,
                                                          "local" if Path(e["path"]).is_file() else "stream"))
                    break
                except Exception as exc:
                    _log("scan %s attempt %d failed: %s" % (e["name"], attempt + 1, str(exc)[:200]))
                    time.sleep(60 * (attempt + 1))
        if DELETE_LOCAL and _scan_path(e["path"]).is_file() and Path(e["path"]).is_file():
            Path(e["path"]).unlink()
            _log("deleted local %s/%s (index kept)" % (e["item"], e["name"]))

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        list(pool.map(one, todo))
    _log("sync done")


def _try(fn, *args):
    try:
        return fn(*args)
    except Exception as exc:
        _log("%s(%s) failed: %s" % (fn.__name__, args, str(exc)[:160]))
        return None


_CACHE = {}


def _scanned():
    """(episode path, embeddings, dark flags) of every scanned episode."""
    rows = []
    for npz in sorted(LIBRARY.glob("*/**/*.siglip.npz")):
        # The episode itself may live only on archive.org (index-only library).
        video = Path(str(npz)[:-len(".siglip.npz")])
        key = (str(npz), npz.stat().st_mtime)
        if key not in _CACHE:
            # One unreadable file used to fail the whole search, and every
            # film ran without the library (library_unavailable BadZipFile,
            # all four CONC films 2026-10-27). It is set aside so the next
            # sync scans the episode again.
            try:
                with open(npz, "rb") as handle:  # closed before a set-aside rename
                    data = np.load(handle)
                    _CACHE[key] = (data["emb"].astype(np.float32), data["dark"])
            except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
                _log("unreadable scan %s set aside: %s" % (npz.name, exc))
                try:
                    os.replace(npz, npz.with_name(npz.name + ".bad"))
                except OSError:
                    pass
                continue
        rows.append((video, *_CACHE[key]))
    return rows


EXPAND_BATCH = 30   # sentences per expansion call (30 took 25 s, 5.5k tokens)


def expand(sentences, folder):
    """Three concrete visual descriptions per sentence, {scene_id: [str]}.

    One Flash call per EXPAND_BATCH sentences, all at once. The library
    is scanned frames, and a narration sentence names little a camera
    sees; three literal descriptions of a matching shot found a PASS in
    the top 3 for 17 of 30 TOPIC_1 sentences against 12 for the sentence
    itself (p@3 PASS 0.22 -> 0.37). Each call's receipt is named by its
    content, so a rerun with the same sentences reads it back. A batch
    that fails leaves its sentences out: they are searched as they are.
    """
    from .io import api
    batches = [sentences[i:i + EXPAND_BATCH] for i in range(0, len(sentences), EXPAND_BATCH)]

    def one(batch):
        prompt = ("A nature documentary needs stock footage for each narration sentence below. For each sentence write "
                  "exactly 3 short, concrete descriptions of what a camera would literally see in a matching shot: the "
                  "animal or object, what it is doing, the setting (water, grass, trees, sky, light). No abstract words, "
                  "no story, no numbers, no place names unless visible; 8-16 words each, each a different plausible shot. "
                  'JSON {"items":[{"id":int,"queries":[string,string,string]}]}\n\n' +
                  "\n".join("%d. %s" % (i, " ".join(str(t).split())) for i, (_, t) in enumerate(batch)))
        receipt = Path(folder) / ("expand_%s.json" % hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:16])
        found = {}
        try:
            data = api("flash", prompt, receipt, tokens=6000, timeout=180)["data"]
            for item in data.get("items") or []:
                queries = [str(q).strip() for q in item.get("queries") or [] if str(q).strip()]
                index = int(item.get("id"))
                if queries and 0 <= index < len(batch):
                    found[batch[index][0]] = queries[:3]
        except Exception:
            pass
        return found

    if not batches:
        return {}
    with ThreadPoolExecutor(max_workers=len(batches)) as pool:
        return {k: v for part in pool.map(one, batches) for k, v in part.items()}


def search(sentences, per_sentence=MAX_PER_SENTENCE, min_fit=MIN_FIT, expansions=None,
           expanded_min_fit=EXPANDED_MIN_FIT):
    """The library moments that show each sentence, best first.

    sentences is [(scene_id, text)]. A sentence with expansions
    ({scene_id: [description]}) is scored by the mean fit of its
    descriptions against expanded_min_fit, the others by their own text
    against min_fit. Returns [{scene_id, path, item, start, end, fit}]
    with at most per_sentence moments a sentence, from different
    episodes or at least a window apart in one.
    """
    library = _scanned()
    if not library or not sentences:
        return []
    from . import picture_fit as pf
    if pf._model() is None:
        return []
    expansions = expansions or {}
    queries = [expansions.get(sid) or [text] for sid, text in sentences]
    floors = np.array([expanded_min_fit if expansions.get(sid) else min_fit for sid, _ in sentences])
    flat = [q for qs in queries for q in qs]
    negatives = list(pf.NEGATIVE)
    texts = pf._texts(flat + negatives).numpy()
    query, neg = texts[: len(flat)], texts[len(flat):]
    # Averages each sentence's columns of the flat query list.
    owner = np.repeat(np.arange(len(sentences)), [len(qs) for qs in queries])
    mean = np.zeros((len(flat), len(sentences)), np.float32)
    mean[np.arange(len(flat)), owner] = 1.0 / np.bincount(owner)[owner]
    found = []
    for video, emb, dark in library:
        sims = (emb @ query.T) @ mean
        fit = sims - pf.PENALTY * (emb @ neg.T).max(1, keepdims=True)
        fit[dark] = -1.0
        # A moment is a run of seconds, not one frame: smoothed over 6 s.
        kernel = np.array([0.25, 0.5, 0.25])
        fit = np.stack([np.convolve(fit[:, j], kernel, "same") for j in range(fit.shape[1])], 1)
        for j in range(fit.shape[1]):
            for i in np.argsort(-fit[:, j])[:per_sentence * 4]:
                if fit[i, j] < floors[j]:
                    break
                found.append((float(fit[i, j]), j, video, i * STEP))
    found.sort(key=lambda r: -r[0])
    result, taken = [], {}
    for score, j, video, second in found:
        mine = taken.setdefault(j, [])
        if len(mine) >= per_sentence or any(v == video and abs(s - second) < WINDOW for v, s in mine):
            continue
        mine.append((video, second))
        result.append({"scene_id": sentences[j][0], "path": str(video), "item": video.parent.name,
                       "start": max(0.0, second - 2.0), "end": second + 6.0, "fit": round(score, 4),
                       "expanded": bool(expansions.get(sentences[j][0]))})
    return result


def cut_windows(matches, out):
    """Cut a WINDOW-second window around each match into the run's sources.

    The windows are written like fetched YouTube windows, with the same
    "<label>.ranges.json" map, so every source-second rule (four cuts a
    recording, thirty seconds apart) and the window index apply to them.
    One label per episode, so one episode is one recording.
    """
    directory = Path(out) / "sources"
    directory.mkdir(parents=True, exist_ok=True)
    by_episode = {}
    for m in matches:
        by_episode.setdefault(m["path"], []).append(m)

    episodes = []
    for path, ms in by_episode.items():
        label = "bbc_" + hashlib.sha1(path.encode()).hexdigest()[:12]
        spans = []
        for m in sorted(ms, key=lambda m: m["start"]):
            centre = (m["start"] + m["end"]) / 2
            a = max(0.0, centre - WINDOW / 2)
            if spans and a < spans[-1][1]:
                spans[-1][2].append(m)
                continue
            spans.append([a, a + WINDOW, [m]])
        episodes.append((path, label, spans))

    def window(job):
        # One window failing (a refused NVENC session, an 'N/A' duration)
        # costs that window only: one bad probe threw away all 98 windows of
        # TOPIC_3 (4.1 GB) when it raised out of the episode loop.
        path, label, i, a, b = job
        target = directory / ("%s_%03d.mp4" % (label, i))
        try:
            if not target.is_file():
                _cut_window(path, a, b, target)
            return _window_length(target, b - a)
        except Exception as exc:
            print("bbc_library: window %s skipped: %s" % (target.name, exc), file=sys.stderr)
            target.unlink(missing_ok=True)
            return 0.0

    # The windows of all episodes are cut in one pool of six: six parallel
    # cuts measured 5.3 s a window, three episodes cut serially 20 s.
    jobs = [(path, label, i, a, b) for path, label, spans in episodes for i, (a, b, _inside) in enumerate(spans)]
    with ThreadPoolExecutor(max_workers=CUT_WORKERS) as pool:
        lengths = dict(zip(((label, i) for _p, label, i, _a, _b in jobs), pool.map(window, jobs)))

    def collect(path, label, spans):
        mapping, rows = [], []
        for i, (a, b, inside) in enumerate(spans):
            target = directory / ("%s_%03d.mp4" % (label, i))
            length = lengths[(label, i)]
            if length <= 1:
                continue
            mapping.append({"source_start": round(a, 3), "source_end": round(a + length, 3), "local_start": 0.0,
                            "local_end": round(length, 3), "length_sec": round(length, 3), "path": str(target)})
            episode = Path(path)
            rows.append({"id": "%s_%03d" % (label, i), "kind": "VIDEO", "path": str(target),
                         "start": round(a, 3), "end": round(a + length, 3), "local_start": 0.0, "local_end": round(length, 3),
                         "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                         "source_url": _remote(episode).replace("/download/", "/details/", 1),
                         "source_title": "BBC %s - %s" % (episode.parent.name, episode.stem),
                         "rights": "BBC, archive.org copy; user holds written clearance",
                         "native_width": 1920, "native_height": 1080,
                         "source_start": round(a, 3), "source_end": round(a + length, 3), "range_file": True,
                         "priority_channel": True, "library": True,
                         "scene_ids": sorted({m["scene_id"] for m in inside}),
                         "library_fit": max(m["fit"] for m in inside)})
        if mapping:
            (directory / (label + ".ranges.json")).write_text(json.dumps(
                {"url": rows[0]["source_url"], "windows": mapping, "source_id": label, "kind": "window_set"}), encoding="utf-8")
        return rows

    return [r for episode in episodes for r in collect(*episode)]


CUT_WORKERS = 6
# Cuts running at once for all films of the process: each is an ffmpeg with
# its own NVENC context (~400 MB). Six a film made 24 at four films, 12.8 GB
# of ffmpeg, free RAM 2 MB and a frozen desktop (CONC_1..4, 2026-10-27).
# Kept across module reloads so every film shares the same slots.
_CUT_SLOTS = globals().get("_CUT_SLOTS") or threading.BoundedSemaphore(
    int(os.environ.get("DOCUMENTARY_BBC_CUTS", "4")))


def _cut_window(path, a, b, target):
    with _CUT_SLOTS:
        _cut_window_now(path, a, b, target)


def _cut_window_now(path, a, b, target):
    # The episode is read from disk if still here, else cut from
    # archive.org (a 32 s 1080p window took 17 s). -g 30 keeps
    # single-frame seeks cheap (3.3x on BBC windows). When NVENC refuses
    # a session the window is encoded with libx264 instead.
    head = ["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % a, "-t", "%.3f" % (b - a), *_input(_source(path)), "-map", "0:v:0", "-an"]
    try:
        subprocess.run([*head, "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "19", "-g", "30", str(target)],
                       check=True, timeout=600, capture_output=True)
    except subprocess.CalledProcessError:
        target.unlink(missing_ok=True)
        subprocess.run([*head, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-g", "30", str(target)],
                       check=True, timeout=600, capture_output=True)


def _window_length(target, planned):
    """The cut window's duration; its planned length when ffprobe twice gives none."""
    for _ in range(2):
        text = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(target)],
                              capture_output=True, text=True).stdout.strip()
        try:
            return float(text)
        except ValueError:
            continue
    return float(planned) if target.is_file() and target.stat().st_size > 0 else 0.0


def status():
    eps = [e for item in ITEMS + tuple(FILTERED_ITEMS) for e in _try(episodes, item) or []]
    scanned = [e for e in eps if _scan_path(e["path"]).is_file()]
    local = [e for e in eps if Path(e["path"]).is_file()]
    print("episodes %d (%.0f GB on archive.org), scanned %d, still on disk %d (%.1f GB)" % (
        len(eps), sum(e["size"] for e in eps) / 1e9, len(scanned), len(local),
        sum(Path(e["path"]).stat().st_size for e in local) / 1e9))


if __name__ == "__main__":
    {"sync": sync, "status": status}[sys.argv[1] if len(sys.argv) > 1 else "status"]()
