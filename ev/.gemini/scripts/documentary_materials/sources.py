"""Real source discovery, content hashes and frame-based inventory."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
from io import BytesIO
import itertools
from itertools import zip_longest
import json
import os
import subprocess
import threading
import requests
import math
import time
from pathlib import Path
import re
import shutil
import bisect
import urllib.parse
import urllib.request
from .control import check_cancelled, set_context
from .reservations import origin_id, MAX_USES_PER_ORIGIN, MAX_USES_PER_MATERIAL, MIN_SAME_ORIGIN_GAP_SECONDS
from . import profiles, resources, yt_cache, yt_gate
import copy

from PIL import Image, ImageDraw, ImageFont, ImageOps
import functools
import yt_dlp
from yt_dlp.networking import common as _yt_networking

# yt-dlp builds an SSL context, loading certifi's whole bundle, for every
# YoutubeDL it opens: 15 percent of the bridge's CPU in a four-film run
# (py-spy, 2026-10-27). The arguments are flags, so one context per flag
# set serves every call; the guard keeps a module reload from wrapping twice.
if not hasattr(_yt_networking.make_ssl_context, "cache_info"):
    _yt_networking.make_ssl_context = functools.lru_cache(maxsize=8)(_yt_networking.make_ssl_context)
import pymupdf

from .io import SCRIPTS, SOURCE_PRIORITY_RULE, LICENSE_OVERLAY_RULE, api, digest, event, load, probe, run, save, sha

FONT = r"C:\Windows\Fonts\arial.ttf"
EXCLUDED = {".git", ".venv", "venv", "node_modules", "_voice_output", "03_materials", "chunks", "pre_repair", "scan_folder_probe_cache.json"}

# Ceiling for one source-classification request. Measured in the production
# run: successful groups answered in a 10.9 s median, but 12 of 27 groups ran
# into the 120 s timeout and fell back to the heuristic classifier, which is
# a quality loss. 45 s keeps the successful path (max observed 16.1 s) and
# cuts the failing tail to a fraction of the old cost.
INVENTORY_TIMEOUT_SECONDS = 45

# After this many seconds a stalled classification gets a second request.
# The production run gave every group exactly one chance, so a group that
# stalled burned the whole 45 s ceiling and then fell back to the local
# heuristic, which is the quality loss the fallback is supposed to avoid:
# 12 of 27 groups (44%) took that path.
#
# The measured effect (bench_classify_hedge.py, synthetic clips, real
# gateway, 16 groups at 15 parallel): without a hedge 4 of 8 groups timed
# out and fell back; with a 25 s hedge 14 of 16 answered cleanly and only
# 2 fell back (12%). The hedge turns a 44% heuristic-classified pool into
# a 12% one without extending the ceiling.
INVENTORY_HEDGE_SECONDS = 25

def contact(tiles, path, columns=3, cell=(420, 270)):
    canvas = Image.new("RGB", (cell[0] * columns, cell[1] * math.ceil(len(tiles) / columns)), "#e9ecef")
    d = ImageDraw.Draw(canvas)
    for i, (file, label) in enumerate(tiles):
        with Image.open(file) as im:
            im = ImageOps.contain(im.convert("RGB"), (cell[0] - 12, cell[1] - 48))
        x, y = (i % columns) * cell[0], (i // columns) * cell[1]
        canvas.paste(im, (x + (cell[0] - im.width) // 2, y + 42))
        d.text((x + 6, y + 4), str(label)[:95], font=ImageFont.truetype(FONT, 16), fill="#14212f")
    canvas.save(path, quality=88)
    return str(path)

def sample(path, seconds, output, width=640):
    # R_ffmpeg_cpu: the same command as before (grab_frames builds it), on the GPU decoder when a
    # slot is free (byte-identical frames), the CPU command otherwise or on any GPU failure.
    resources.grab_frames(path, [(seconds, output)], width, 30)
    with Image.open(output) as im:
        im.verify()
    return str(output)

def samples(path, seconds_list, outputs, width=640):
    """Extract several frames from one clip in a single ffmpeg pass.

    The per-shot review board takes one sample per second of shot duration.
    Calling sample() for each of them spawns one ffmpeg process per frame:
    the production run measured 1.13 s of process time for 8 frames of a
    6.7 s shot, which is ~186 s across 165 shots. One select pass produces
    the same frames in 0.16 s, so the whole ledger costs 27 s instead.

    The select expression indexes source frames, so the extracted frame is
    the exact one at the requested timestamp instead of the first frame at or
    after it.
    """
    seconds_list = [float(s) for s in seconds_list]
    if not seconds_list:
        return []
    rate = _frame_rate(path)
    frames = [int(round(max(0.0, s) * rate)) for s in seconds_list]
    unique = sorted(set(frames))
    index_of = {frame: i for i, frame in enumerate(unique)}
    produced = [Path(outputs[index_of[f]]) for f in frames]
    unique_outputs = [Path(outputs[index_of[f]]) for f in unique]
    for target in unique_outputs:
        target.parent.mkdir(parents=True, exist_ok=True)
    expression = "+".join("eq(n\\,%d)" % f for f in unique)
    stem = unique_outputs[0].parent / (unique_outputs[0].stem + "_%03d.jpg")
    # A previous attempt may have left the temporary frames behind; a stale
    # file would corrupt the frame count check below.
    for stale in unique_outputs[0].parent.glob(unique_outputs[0].stem + "_*.jpg"):
        stale.unlink()
    try:
        proc = resources.decode_run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(path),
             "-vf", f"select='{expression}',scale={width}:-1", "-fps_mode", "passthrough",
             "-pix_fmt", "yuvj420p", str(stem)], timeout=60, cuda="exact")
        if proc.returncode:
            raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[-2200:])
    except Exception:
        # Any single-pass failure falls back to the per-frame path, which is
        # slower but always correct.
        for seconds, output in zip(seconds_list, produced):
            sample(path, seconds, output, width)
        return [str(p) for p in produced]
    extracted = sorted(unique_outputs[0].parent.glob(unique_outputs[0].stem + "_*.jpg"))
    if len(extracted) != len(unique):
        for seconds, output in zip(seconds_list, produced):
            sample(path, seconds, output, width)
        return [str(p) for p in produced]
    for target, source in zip(unique_outputs, extracted):
        if target != source:
            source.replace(target)
    for output in produced:
        with Image.open(output) as im:
            im.verify()
    return [str(p) for p in produced]

_FRAME_RATE_CACHE = {}

def _frame_rate(path):
    key = str(path)
    cached = _FRAME_RATE_CACHE.get(key)
    if cached:
        return cached
    try:
        stream = next(s for s in probe(path).get("streams", []) if s.get("codec_type") == "video")
        numerator, _, denominator = str(stream.get("avg_frame_rate", "0/1")).partition("/")
        rate = float(numerator) / max(1.0, float(denominator or 1))
        if rate <= 0:
            rate = 25.0
    except Exception:
        rate = 25.0
    _FRAME_RATE_CACHE[key] = rate
    return rate

def _partial_format(height=1080):
    """The format selector used for a partial download.

    A partial download uses the mp4_dash formats, which are plain
    progressive mp4 files on the CDN and support byte range requests.
    The m3u8 (HLS) formats do not, and the "best[height<=720]" selector
    picks an HLS stream, which is why the first attempt at a section
    download failed with "Requested format is not available".

    The height is the same 1080p, 720p, 480p order the whole-file
    download uses, so the film gets the same resolution whether the
    source was fetched whole or in windows.
    """
    # avc1 first: at 1080p it fetched 16 sources in 30.7 s, where the
    # ladder's AV1/VP9 4K streams took 103.6 s for 70% more bytes.
    return (f"bestvideo[height<={height}][ext=mp4][vcodec^=avc1][format_id!*=hls]/"
            f"bestvideo[height<={height}][ext=mp4][format_id!*=hls]/"
            f"best[height<={height}][ext=mp4]")

# The resolutions the film accepts, best first. The film is 1080p, but
# a 4K source that is scaled down to it carries more detail than a
# 1080p source scaled to it, and the frame that reaches the picture is
# better. The list is a preference, not a demand: the first height the
# source actually publishes is the one that is fetched, and a source
# that publishes nothing larger is fetched at the height it has.
QUALITY_HEIGHTS = (2160, 1440, 1080, 720, 480)


def _partial_heights(prefer_height=1080):
    """The resolution order of a partial download.

    The whole-file download walks the same ladder and falls back only
    when the source publishes nothing larger. The partial path has to
    walk the same ladder, because a DASH mp4 is not always there
    either: a source that only publishes a progressive 360p stream has
    no DASH mp4 at all, and the first selector would fail the whole
    window fetch instead of falling back.
    """
    # prefer_height is a ceiling for windows: the 2160/1440 rungs made 20
    # of 51 windows 4K or 1440p, 110-330 MB a source against 25-65 MB.
    heights = [h for h in QUALITY_HEIGHTS if h <= (prefer_height or 2160)]
    if prefer_height and prefer_height not in heights:
        heights.append(prefer_height)
    return heights

# ---------------------------------------------------------------------------
# PARTIAL DOWNLOAD LAYER
#
# Measured on the delivered run:
#   9.05 GB were downloaded across 168 sources
#   287.5 s of video reached the film, which is 1.2 percent of the
#   downloaded footage
#
# A window download of three 20 second windows of a 1080p source
# transfers 4.1 MB against 61 MB for the whole file, and the result
# is aligned: the frames of the window match the frames of the full
# file at the same second with a PSNR of 42.3 to 45.7 dB, measured
# against the full 1080p download.
#
# Two facts make the replacement safe:
#   1) the source audio is never used. Every cut into a source video
#      runs with "-an" and the only audio in the film is the narration
#      master, so a video-only window file loses nothing.
#   2) the source time is what the rules are written against. The
#      overlap rule, the use cap and the motion check all work on the
#      source second, so the local file only has to carry the same
#      picture at the same source second.
#
# The cut is exact without a re-encode. yt-dlp's section download
# without force_keyframes_at_cuts produced frames that were bit
# identical to the source (PSNR 99), and the window's own duration
# matched the request to within one frame. The re-encode variant
# costs 47.6 s against 44.9 s for the same three windows and buys
# nothing measurable, so it is off.
# ---------------------------------------------------------------------------

# The windows a source is fetched for. The value is the padding around
# the cut that the film actually needs. A cut of 5 s is fetched with
# 3 s of headroom and 3 s of tail, because the freeze check may move
# the start of a window and the render may need one extra frame.
RANGE_PADDING_SECONDS = 3.0

# The shortest window worth fetching. Below this the overhead of a
# second request is not worth the bytes saved.
RANGE_MIN_SECONDS = 6.0

# The longest window one request may cover. YouTube serves a range
# from one URL, so a longer window costs the same in requests but
# more in bytes.
RANGE_MAX_SECONDS = 120.0

# The number of windows one source may be fetched with. A source that
# needs more is fetched whole, because the request overhead is what
# the range layer is trying to avoid.
RANGE_MAX_WINDOWS = 4

# The width of the single window a source is fetched with. The film
# cuts its footage from a narrow band: over the 60 camera cuts of the
# delivered film the median distance between the cut and the middle
# of its source was 5.4 seconds, and 57 of the 60 cuts sat within 30
# seconds of the middle. A 32 second window covers 57 of the 60 cuts.
#
# Two narrow windows of 26 seconds covered 54 of the 60, because the
# second one sat a quarter of the way into the source and the film
# almost never cut there. One wide window therefore covers more of
# the film than the two narrow ones, and it costs one request instead
# of two.
#
# The cost was measured over the job's 75 sources at eight parallel,
# with the production socket timeout of 30 seconds:
#
#   1 window of 26 s   189.7 s   75/75   311 MB   <- this one
#   2 windows of 26 s  152.4 s   74/75   501 MB
#   1 window of 38 s   204.9 s   75/75   360 MB
#   whole file         283.0 s          8290 MB
#
# The two window run was a second slower and lost a source to an
# ffmpeg timeout, so the second window bought no time and cost a
# failure. The 38 second window costs 15 seconds more than the 26
# second one and covers three cuts more, so it is not worth the
# seconds.
#
# The 26 second span with the three second padding on each side, so
# a 32 second file, is the shape: it covers the same 57 of the 60
# cuts of the delivered film as the 38 second file, and it fetches
# 93 seconds and 7.8 GB less than the whole file.
RANGE_WIDE_SECONDS = 26.0

# The length of one scene window. The scene scan of a long source cuts
# it into windows of this length, and the excerpt the film uses is cut
# out of one of them, so a fetched window has to cover a whole scene
# window and not only the excerpt.
SCENE_WINDOW_SECONDS = 14.0

def _range_windows(start, end):
    """The padded window that covers a cut."""
    a = max(0.0, float(start) - RANGE_PADDING_SECONDS)
    b = float(end) + RANGE_PADDING_SECONDS
    if b - a < RANGE_MIN_SECONDS:
        b = a + RANGE_MIN_SECONDS
    if b - a > RANGE_MAX_SECONDS:
        b = a + RANGE_MAX_SECONDS
    return a, b

# YouTube refused the run as a bot after ~40 requests ("Sign in to confirm
# you're not a bot", 138 errors in one TOPIC_2 run). A proof-of-origin
# token from the bgutil provider, with the mweb client beside the default
# ones, passed 8 of 8 metadata reads from the flagged IP where the default
# path passed 0 of 8, with 1080p avc1 and the storyboards intact. The
# provider is a local node server; without it yt-dlp quietly drops to
# 360p, so ensure_pot_server starts it before a run fetches anything.
POT_URL = os.environ.get("BGUTIL_POT_URL", "http://127.0.0.1:4416")
POT_SERVER = Path(os.environ.get("BGUTIL_POT_SERVER", "C:/Users/meteh/tools/bgutil-pot/server/build/main.js"))
#
# The default clients only (2026-10-27): mweb beside them on every video
# was a second player request and a second PO token per video, so it is
# asked only when the default extraction fails or has no mp4 stream
# (_youtube_info).
YOUTUBE_ARGS = {"youtube": {"player_client": ["default"]},
                "youtubepot-bgutilhttp": {"base_url": [POT_URL]}}
FALLBACK_CLIENTS = ["default", "mweb"]
_pot_lock = threading.Lock()
_pot_seen = [0.0]


def _yt_common():
    """The options every yt-dlp call to YouTube shares.

    The challenge solver runs on node with the EJS script (yt-dlp-ejs, or
    fetched once from yt-dlp's GitHub); without it the format list
    collapses. yt-dlp sleeps a second between the requests of one call
    (DOCUMENTARY_YT_SLEEP_REQUESTS), and an extractor error is retried
    once, after 10 s (exponential up to 300 s), as yt-dlp's FAQ advises
    for a soft block. Account cookies come from a browser profile only
    when DOCUMENTARY_YT_COOKIES_BROWSER names one.
    """
    opts = {"js_runtimes": {"node": {}}, "remote_components": ["ejs:github"],
            "sleep_interval_requests": float(os.environ.get("DOCUMENTARY_YT_SLEEP_REQUESTS", "1")),
            "extractor_retries": 1,
            "retry_sleep_functions": {"extractor": lambda n: min(300, 10 * 2 ** n)}}
    if yt_gate.COOKIES_BROWSER:
        browser, _, profile = yt_gate.COOKIES_BROWSER.partition(":")
        opts["cookiesfrombrowser"] = (browser, profile or None, None, None)
    return opts


def _pot_alive():
    try:
        return requests.get(POT_URL + "/ping", timeout=3).ok
    except Exception:
        return False


def ensure_pot_server(out=None):
    """Start the local PO token server when it is not answering.

    The server took more than 10 s to answer its first ping, so the wait
    is up to 60 s.
    """
    with _pot_lock:
        if _pot_alive():
            _pot_seen[0] = time.monotonic()
            return True
        if POT_SERVER.is_file():
            subprocess.Popen(["node", str(POT_SERVER), "-H", "127.0.0.1"], cwd=str(POT_SERVER.parent.parent),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            for _ in range(120):
                time.sleep(0.5)
                if _pot_alive():
                    _pot_seen[0] = time.monotonic()
                    return True
        if out is not None:
            event(out, "pot_server_unavailable", server=str(POT_SERVER))
        return False


def _pot_ready(out=None):
    """The PO token server answers before a player request (checked once a minute)."""
    if time.monotonic() - _pot_seen[0] > 60:
        ensure_pot_server(out)


def _is_bot_check(exc):
    return "not a bot" in str(exc) or "Sign in to confirm" in str(exc)


_YOUTUBE_ID = re.compile(r"(?:[?&]v=|youtu\.be/|/shorts/|/embed/)([\w-]{11})")


def _youtube_id(url):
    """The video id of a YouTube watch URL, or None."""
    found = _YOUTUBE_ID.search(str(url or ""))
    return found.group(1) if found else None


def _film_of(folder):
    """The film folder a search folder (searches/..., source_recovery/...) belongs to."""
    parts = Path(folder).parts
    for marker in ("searches", "source_recovery"):
        if marker in parts:
            return Path(*parts[:parts.index(marker)])
    return Path(folder)


# Errors of the video itself, which another request does not change.
_GONE = ("Video unavailable", "Private video", "This video has been removed", "members-only",
         "Join this channel", "confirm your age", "account associated with this video has been terminated",
         "This live event", "Premieres in", "copyright claim")


def _youtube_info(url, out, fresh=False):
    """The full extraction of a YouTube video, from the cache or one gated request.

    The probe and every download of the same video share it: a download
    re-runs the format selection on it locally, which is what yt-dlp's
    --load-info-json does, so the height ladder and the chunked retry no
    longer extract the page again for every rung.
    """
    video_id = _youtube_id(url)
    if not fresh:
        info = yt_cache.get_info(video_id)
        if info is not None:
            return info
    _pot_ready(out)

    def extract(clients):
        opts = {"quiet": True, "no_warnings": True, "skip_download": True,
                "socket_timeout": 15, "retries": 2, **_yt_common(),
                "extractor_args": {**YOUTUBE_ARGS, "youtube": {"player_client": clients}}}
        with yt_dlp.YoutubeDL(opts) as y:
            found = y.extract_info(url, download=False)
            return y.sanitize_info(found, remove_private_keys=True) if found else None

    def has_mp4(found):
        return any(f.get("ext") == "mp4" and f.get("vcodec") not in (None, "none") and f.get("height")
                   for f in (found or {}).get("formats") or [])

    def extract_with_fallback():
        # The default clients first; mweb (with its own PO token) only
        # when they fail or give no mp4 stream the window fetch can use.
        # A video that is gone is gone for every client.
        try:
            found = extract(YOUTUBE_ARGS["youtube"]["player_client"])
        except Exception as exc:
            if any(k in str(exc) for k in _GONE):
                raise
            return extract(FALLBACK_CLIENTS)
        return found if has_mp4(found) else (extract(FALLBACK_CLIENTS) or found)
    info = yt_gate.call("metadata", extract_with_fallback, out)
    if info:
        yt_cache.put_info(video_id or info.get("id"), info)
    return info


def _stale_urls(exc):
    text = str(exc)
    return "HTTP Error 403" in text or "HTTP Error 410" in text or "expired" in text.lower()


def _ydl_download(url, opts, out):
    """Download with opts from the shared extraction; returns (info, path).

    Only the media is read here (the CDN), so no request slot is taken;
    a pause still holds it. Format URLs the CDN refuses are extracted
    once more; a second refusal is YouTube's and pauses every call.
    """
    for fresh in (False, True):
        info = _youtube_info(url, out, fresh=fresh)
        if not info:
            raise FileNotFoundError("Source metadata could not be read")
        yt_gate.wait_clear(out)
        began = time.time()
        try:
            with yt_dlp.YoutubeDL(opts) as y:
                done = y.process_ie_result(copy.deepcopy(info), download=True)
                return done, Path(y.prepare_filename(done))
        except Exception as exc:
            if not _stale_urls(exc):
                raise
            if fresh:
                yt_gate.report(exc, "media", out, began)
                raise
            yt_cache.drop_info(_youtube_id(url))


def _dl_opts(fmt, outtmpl, ranges=None, clients=None, fragments=8, chunked=True):
    """The shared yt-dlp options.

    The player client matters, but not the way it first appears. The
    android client is faster on paper: the same 1080p request took
    2.22 s with it and 5.14 s without. It is also 4.3 times smaller.
    The reason is that the android client does not serve the DASH
    streams: it offers only format 18, a progressive 640x360 file. So
    the speed comes from a lower resolution, and the default client is
    the one that can actually deliver 720p and 1080p.

    The range path needs a DASH mp4, which the android client does not
    serve, so the two cannot be combined.

    A JavaScript runtime is required to resolve the YouTube player
    signature. Without it the extractor falls back, the format list
    collapses and the download silently drops to 360p.

    The socket timeout is 30 seconds, not 15. The two window run over
    the job's 75 sources lost one source to "ffmpeg exited with code
    3436169992", which is the Windows timeout status, while the one
    window run over the same sources lost none. A 15 second socket
    timeout is too tight when eight ffmpeg processes read the CDN at
    the same time: one slow answer is read as a dead connection, and
    the source is lost.
    """
    opts = {"quiet": True, "noprogress": True, "no_warnings": True,
            "socket_timeout": 30, "retries": 2, **_yt_common(),
            "format": fmt, "noplaylist": True, "outtmpl": str(outtmpl),
            "nopart": True, "concurrent_fragment_downloads": fragments}
    opts["extractor_args"] = {**YOUTUBE_ARGS, "youtube": {"player_client": list(clients) if clients
                                                         else YOUTUBE_ARGS["youtube"]["player_client"]}}
    if ranges is not None:
        opts["download_ranges"] = ranges
    if ranges is not None and chunked:
        # A section is read by ffmpeg, which asks the CDN for everything
        # from the seek point on in one request, and YouTube serves such
        # an open request at about 4.4 MB/s once its first 10 MB are out:
        # measured, a 40 MB range took 9.0 s and a 10 MB range 0.4 s.
        # yt-dlp's own downloader asks in 10 MiB chunks for this reason,
        # and ffmpeg can do the same. A 64 MB window of a 4K source took
        # 16.3 s without and 4.1 s with it, and the file was identical
        # (same md5). Sixteen Gotthard sources, eight at a time, went
        # from 130 s to 44 s, with every window file byte-identical; the
        # line, not the stream, is now the limit.
        # yt-dlp passes ffmpeg no timeout (socket_timeout never reaches
        # it), and one read hung a benchmark source for nine minutes.
        opts["external_downloader_args"] = {"ffmpeg_i": [
            "-rw_timeout", "15000000", "-reconnect", "1", "-reconnect_on_network_error", "1",
            "-reconnect_delay_max", "4", "-request_size", str(10 << 20)]}
    return opts

def _windows_hold_video(directory, label, windows):
    """True when every window file carries video for its whole range.

    A chunked section fetch came back, now and then, as files with no
    stream at all (261 bytes, ffmpeg exit 0): 4 of 112 sources over the
    test runs, always every window of the source. The file is checked
    here with its own ffprobe, not the cached probe(), because a failed
    file is fetched again under the same name.
    """
    for i, (a, b) in enumerate(windows):
        f = directory / (label + "_%03d.mp4" % i)
        if not f.is_file():
            return False
        try:
            found = json.loads(resources.probe_run(
                ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                 "stream=codec_type:format=duration", "-of", "json", f], 30).stdout or "{}")
        except Exception:
            return False
        if not found.get("streams") or float((found.get("format") or {}).get("duration") or 0) < b - a - 1.0:
            return False
    return True

def _download_windows(url, out, windows, label, clients=None, fragments=8,
                      prefer_height=1080, media_url=None):
    """Fetch only the given windows of a video, as separate local files.

    The windows are fetched in one extractor call, so the per-call
    overhead is paid once and the extractor resolves the player
    signature once. yt-dlp writes one file per section, so the result
    is one file per window plus a map from the source second to the
    local second.

    The section download is not re-encoded. Measured against the full
    1080p download, the frames of every window matched the source at
    the same second with a PSNR of 42.3 to 45.7 dB, and the window's
    own duration matched the request to within one frame.

    Returns (path, map) or (None, None) when the fetch did not work.
    """
    directory = Path(out) / "sources"
    directory.mkdir(exist_ok=True)
    sidecar = directory / (label + ".ranges.json")
    requested = [[round(a, 3), round(b, 3)] for a, b in windows]
    if sidecar.is_file():
        try:
            cached = load(sidecar)
            # The cache holds only when it holds the windows asked for. A
            # sidecar from another window plan, or one written by hand,
            # used to be returned as it was, so the run cut from windows
            # it never planned.
            if cached.get("url") == url and [[w["source_start"], w["source_end"]] for w in cached.get("windows") or []] == requested:
                files = [Path(directory / (label + "_%03d.mp4" % i))
                         for i in range(len(cached["windows"]))]
                if all(f.is_file() and f.stat().st_size > 0 for f in files):
                    return files, cached
        except Exception:
            pass
    # The section files of an older plan would be taken as already
    # downloaded, so they leave before the new windows are fetched.
    for stale in list(directory.glob(label + "_*")) + [sidecar]:
        try:
            stale.unlink()
        except OSError:
            pass

    # A window another film (or an earlier run) fetched is taken from the
    # shared cache; only the rest is fetched.
    source_key = label[:-len("_windows")] if label.endswith("_windows") else label
    height_key = "media" if media_url else prefer_height
    entries = [yt_cache.window_entry(source_key, a, b, height_key) for a, b in windows]
    missing = [i for i, entry in enumerate(entries)
               if not yt_cache.take(entry, directory / (label + "_%03d.mp4" % i))]
    if len(missing) < len(windows):
        event(out, "range_cache_hit", id=label, cached=len(windows) - len(missing), fetched=len(missing))

    def clear_missing():
        for i in missing:
            try:
                (directory / (label + "_%03d.mp4" % i)).unlink()
            except OSError:
                pass

    def ranges(info_dict, ydl):
        for i in missing:
            a, b = windows[i]
            yield {"start_time": float(a), "end_time": float(b), "index": i}

    # The section path needs a DASH mp4, which only the default client
    # serves. The android client is faster but serves a progressive
    # 360p file, and a range cannot be cut out of a progressive
    # download without the whole file, so the two are not combined.
    template = directory / (label + "_%(section_number)03d.%(ext)s")
    downloaded = not missing
    last_error = ""
    # An archive file is one URL with one resolution, chosen when it was
    # probed, so it has no ladder to walk. ffmpeg reads only the bytes
    # of each window over range requests, and the stream copy keeps the
    # cut as exact as yt-dlp's own section download, which runs the
    # same ffmpeg command: measured against a frame-exact decode of the
    # remote file at the same second, the window's frame was identical.
    for height in [] if not missing else [None] if media_url else _partial_heights(prefer_height):
        try:
            if media_url:
                source, remote = media_url, _HTTP_INPUT
                if urllib.parse.urlparse(media_url).netloc in _WHOLE_FILE_HOSTS:
                    source, remote = directory / (label + "_whole.part"), []
                    _fetch_whole(media_url, source)
                try:
                    for i in missing:
                        a, b = windows[i]
                        run(["ffmpeg", "-v", "error", "-y", *remote, "-ss", a, "-t", b - a, "-i", source,
                             "-map", "0:v:0", "-c", "copy", "-an", directory / (label + "_%03d.mp4" % i)], 300)
                finally:
                    if not remote:
                        Path(source).unlink(missing_ok=True)
            else:
                # The chunked fetch first; when its files come back
                # without video, the same height once more as one
                # stream, which is how every window was fetched before.
                # Both, and every rung of the ladder, select their format
                # from the one shared extraction (_ydl_download).
                for chunked in (True, False):
                    opts = _dl_opts(_partial_format(height), template, ranges=ranges,
                                    clients=clients, fragments=fragments, chunked=chunked)
                    _ydl_download(url, opts, out)
                    if not chunked or _windows_hold_video(directory, label, windows):
                        break
                    event(out, "range_download_chunked_retry", id=label)
                    clear_missing()
            downloaded = True
            break
        except Exception as exc:
            # A height that the source does not publish fails the
            # request, and the next height is tried. The last failure
            # is reported so the caller can fall back to the whole file.
            last_error = "%s: %s" % (type(exc).__name__, str(exc)[:120])
            clear_missing()
            # A bot refusal is the same at every height; walking the
            # ladder only spent more requests against the block.
            if _is_bot_check(exc) or yt_gate.throttled(exc) or isinstance(exc, yt_gate.YouTubeBlocked):
                break
    if not downloaded:
        for i in range(len(windows)):
            if i not in missing:
                try:
                    (directory / (label + "_%03d.mp4" % i)).unlink()
                except OSError:
                    pass
        event(out, "range_download_failed", id=label, error="DownloadError",
             detail=last_error[:200])
        return None, None
    files = sorted(directory.glob(label + "_*.mp4"))
    if not files or any(f.stat().st_size == 0 for f in files):
        event(out, "range_download_empty", id=label, files=len(files))
        return None, None
    if len(files) != len(windows):
        # The extractor wrote a different number of files than windows.
        # The map would be wrong, so the caller falls back to the whole
        # file rather than to a mislabelled one.
        event(out, "range_download_count_mismatch", id=label,
             expected=len(windows), got=len(files))
        return None, None
    # The map is built from the measured duration of each window, not
    # from the requested one, so a window that came back a frame short
    # still maps exactly.
    #
    # Every window is its own file, so its own local second zero is
    # the start of its own source range. The files are NOT one
    # timeline laid end to end: each file starts at the source second
    # it was fetched for.
    mapping = []
    total = 0.0
    for i, ((a, b), f) in enumerate(zip(windows, files)):
        length = float((probe(f).get("format") or {}).get("duration") or 0)
        if length <= 0:
            return None, None
        # The checked window is kept for the next film; "cache" names the
        # shared file, whose index and fingerprints every film then shares.
        shared = yt_cache.store(f, entries[i]) if i in missing else entries[i]
        mapping.append({"source_start": round(a, 3), "source_end": round(b, 3),
                        "local_start": 0.0,
                        "local_end": round(length, 3),
                        "length_sec": round(length, 3),
                        "path": str(f),
                        **({"cache": str(shared)} if shared else {})})
        total += length
    payload = {"url": url, "windows": mapping, "source_id": label,
               "bytes": sum(f.stat().st_size for f in files),
               "duration_sec": round(total, 3),
               "kind": "window_set"}
    save(sidecar, payload)
    event(out, "range_download_ok", id=label, windows=len(windows),
          bytes=payload["bytes"], duration_sec=payload["duration_sec"])
    return files, payload

# ---------------------------------------------------------------------------
# TIME MAPPING
#
# Every rule in the pipeline is written against the SOURCE second: the
# overlap rule, the use cap, the motion check and the freeze check all
# read asset["start"] and asset["end"]. A range download changes where
# that picture lives on disk, not which second of the source it is.
#
# So a range file carries a map, and the mapping is applied in one
# place, here, instead of at every read site. A file that is not a
# range download has no map and its source second is its local second.
# ---------------------------------------------------------------------------

_RANGE_MAPS = {}

def register_range_map(path, payload):
    """Remember the source-to-local map of a fetched window."""
    if path and payload:
        _RANGE_MAPS[str(Path(path))] = payload

def _range_map(path):
    """The source-to-local map of a fetched window, from memory or disk.

    The map is written to a sidecar file next to the window when the
    window is fetched, so it survives the process that downloaded it.
    The render stage runs in the same process as the download, but a
    resumed run reads the windows from disk without downloading them
    again. In that case the memory map is empty and the sidecar is the
    only place the mapping still exists. Without it the render reads a
    fetched window at its source second instead of its local second,
    which is past the end of a 32 second file.
    """
    key = str(Path(path))
    mapping = _RANGE_MAPS.get(key)
    if mapping:
        return mapping
    window = Path(path)
    # The sidecar is named after the window set, not the window file:
    # "<label>.ranges.json" next to "<label>_000.mp4".
    label = window.stem.rsplit("_", 1)[0] if "_" in window.stem else window.stem
    sidecar = window.with_name(label + ".ranges.json")
    if not sidecar.is_file():
        return None
    try:
        payload = load(sidecar)
    except Exception:
        return None
    if not payload or not payload.get("windows"):
        return None
    _RANGE_MAPS[key] = payload
    return payload

def local_time(path, source_second):
    """The local second of a source second inside a fetched window.

    For a file that was not fetched as a window, the source second is
    the local second.
    """
    mapping = _range_map(path)
    if not mapping:
        return float(source_second)
    p_res = str(Path(path).resolve()).lower()
    target_windows = [w for w in (mapping.get("windows") or []) if str(Path(w.get("path", "")).resolve()).lower() == p_res]
    candidate_windows = target_windows if target_windows else (mapping.get("windows") or [])
    for w in candidate_windows:
        if w["source_start"] - 0.05 <= source_second <= w["source_end"] + 0.05:
            return source_second + (w["local_start"] - w["source_start"])
    # Outside every window: the file does not carry that second, so the
    # nearest edge is the honest answer and the caller can detect it.
    if candidate_windows:
        w = min(candidate_windows,
                key=lambda x: min(abs(source_second - x["source_start"]),
                                  abs(source_second - x["source_end"])))
        return source_second + (w["local_start"] - w["source_start"])
    return float(source_second)

def shared_window(path):
    """The shared cache file (yt_cache) a fetched window is a link of, or None."""
    mapping = _range_map(path)
    if not mapping:
        return None
    p_res = str(Path(path).resolve()).lower()
    for w in mapping.get("windows") or []:
        if w.get("cache") and str(Path(w.get("path", "")).resolve()).lower() == p_res:
            return w["cache"] if yt_cache.same_file(path, w["cache"]) else None
    return None

def is_range_file(path):
    """True when the file is a fetched window, not a whole source."""
    return _range_map(path) is not None

def covers_source_second(path, source_second, duration=0.0):
    """True when the file really carries the given source second.

    This is the gate that a fetched window has to pass before it is
    used. A whole source carries every second. A fetched window only
    carries the seconds it was fetched for, so a cut that falls
    outside the window is a real error and not a rounding difference.
    """
    mapping = _range_map(path)
    if not mapping:
        return True
    req_end = source_second + max(0.0, float(duration))
    p_res = str(Path(path).resolve()).lower()
    target_windows = [w for w in (mapping.get("windows") or []) if str(Path(w.get("path", "")).resolve()).lower() == p_res]
    candidate_windows = target_windows if target_windows else (mapping.get("windows") or [])
    for w in candidate_windows:
        if (w["source_start"] - 0.05 <= source_second) and (req_end <= w["source_end"] + 0.05):
            return True
    return False

def _local_bounds(row):
    """The local second range of a row, for reading the file.

    A whole source is read at its own second. A fetched window is
    read at the local second of the window, which is not the source
    second.
    """
    if row.get("range_file"):
        return (float(row.get("local_start", 0.0)),
                float(row.get("local_end", row.get("end", 0.0))))
    return (float(row.get("start", 0.0)), float(row.get("end", 0.0)))

# SearXNG runs on the VDS over Tailscale (2026-11-15: 46 vs 29 web, 371 vs
# 148 image results per query against the PC container, same latency; frees
# Docker Desktop + WSL RAM on the PC). The PC container stays as fallback.
SEARXNG_LOCAL = "http://127.0.0.1:8888"
SEARXNG_BASE = (os.environ.get("DOCUMENTARY_SEARXNG") or "http://100.104.78.117:8888").rstrip("/")


def ensure_searxng(out=None, wait=180):
    """Bring the local SearXNG (Docker container "searxng") up if it is down.

    After a reboot Docker Desktop did not start, SearXNG was down, and the
    Blackout film collected no photograph at all: its 54 PHOTO and CARD
    shots all failed on an empty pool. Returns True when SearXNG answers.
    """
    global SEARXNG_BASE
    import requests as req

    def up(base):
        try:
            return req.get(base + "/search?q=test&format=json", timeout=8).ok
        except Exception:
            return False

    def warm():
        # The image engines answer the first query of a film with 200 and
        # zero results while they warm up (EP02, 2026-11-06: 0 at 15:25,
        # 73 at 15:33 for the same query); one images query in the
        # background, right at stage-3 start, costs nothing on the film.
        def go():
            try:
                req.get(SEARXNG_BASE + "/search?q=archive+photograph&categories=images&format=json", timeout=30,
                        headers={"User-Agent": "documentary-materials/1.0"})
            except Exception:
                pass
        threading.Thread(target=go, name="searxng-warm", daemon=True).start()

    if up(SEARXNG_BASE):
        warm()
        return True
    if out is not None and SEARXNG_BASE != SEARXNG_LOCAL:
        event(out, "searxng_remote_down", detail=SEARXNG_BASE + " not answering; starting the local container")
    docker = Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe")
    if docker.is_file():
        subprocess.Popen([str(docker)], creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    deadline = time.time() + wait
    while time.time() < deadline:
        subprocess.run(["docker", "start", "searxng"], capture_output=True, timeout=60)
        if up(SEARXNG_LOCAL):
            SEARXNG_BASE = SEARXNG_LOCAL
            warm()
            if out is not None:
                event(out, "searxng_started")
            return True
        time.sleep(10)
    if out is not None:
        event(out, "searxng_down", detail="photos cannot be searched; PHOTO and CARD shots will fall back")
    return False


def searxng_images(query, out, limit=60, timeout=8, engine="images"):
    """Search the local SearXNG for real photographs of the subject.

    The documentary is not a synthetic 3D piece. It has to smell of
    real history, and the only way to get real history is to fetch
    real photographs of it. The machine runs a SearXNG instance on
    port 8888, and one image query for "Hyatt Regency walkway collapse
    construction" returned 121 results with real archive photographs
    at 1765x1440, 3000x1688 and 1767x1013.

    The pool is a supplement, not a replacement. When the material
    already in hand is short of photographs, this fetches more. It
    never turns a running job into a 3D job, because the plan is
    written before the pool is complete and the flow of the film must
    not depend on how much material was found.
    """
    url = "%s/search?q=%s&categories=%s&format=json" % (
        SEARXNG_BASE, urllib.parse.quote_plus(query), engine)
    import requests as req
    # The first, long title query of a film timed out at 8 s in every film of the 5 Nov batch and the
    # same query answered minutes later (engines warming); one retry with a longer wait, timeouts only.
    # A 200 with zero results is the same warm-up seen from the other side (EP02, 2026-11-06: the
    # title query answered 0 at 15:25 and 73 at 15:33, and the empty pool made the mix infeasible),
    # so an empty answer is asked again after a short wait, SEARXNG_EMPTY_RETRIES times.
    payload = error = None
    waits = [timeout] + [max(timeout, 25)] * (1 + SEARXNG_EMPTY_RETRIES)
    empty_retries = 0
    for wait in waits:
        try:
            response = req.get(url, timeout=wait,
                               headers={"User-Agent": "documentary-materials/1.0"})
            response.raise_for_status()
            payload = response.json()
        except req.exceptions.Timeout as exc:
            error = exc
            continue
        except Exception as exc:
            error = exc
            break
        if (payload.get("results") if isinstance(payload, dict) else None) or empty_retries >= SEARXNG_EMPTY_RETRIES:
            break
        empty_retries += 1
        event(out, "searxng_empty_retry", query=query, attempt=empty_retries, wait_seconds=SEARXNG_EMPTY_WAIT)
        time.sleep(SEARXNG_EMPTY_WAIT)
    if not isinstance(payload, dict):
        event(out, "searxng_unavailable", query=query,
             error=type(error).__name__, detail=str(error)[:160])
        return []
    results = payload.get("results") or []
    event(out, "searxng_results", query=query, count=len(results), empty_retries=empty_retries)
    return results[:limit]


# How many times an empty (HTTP 200, 0 results) answer is asked again, and the wait between asks.
SEARXNG_EMPTY_RETRIES = max(0, int(os.environ.get("DOCUMENTARY_SEARXNG_EMPTY_RETRIES", "2") or 0))
SEARXNG_EMPTY_WAIT = float(os.environ.get("DOCUMENTARY_SEARXNG_EMPTY_WAIT", "20") or 20)
# The shorter fallback query: a title query of a dozen words can be too specific for the image
# engines; the first words of it (the subject) find the archive photographs the long one missed.
SEARXNG_FALLBACK_WORDS = 6


def fallback_photo_query(query, words=SEARXNG_FALLBACK_WORDS):
    """The shorter query tried when the full one found nothing, or None when it would be the same."""
    parts = [w for w in re.split(r"\s+", str(query or "").strip()) if w]
    if len(parts) <= words:
        return None
    return " ".join(parts[:words])

def fetch_archive_photos(query, out, wanted=24, timeout=20):
    """Fetch real photographs of the subject into the job's photo pool.

    Every candidate is a real photograph from a real page, and the
    file is stored with the page it came from, so the provenance of
    every picture in the film stays readable.
    """
    directory = Path(out) / "photos" / "archive"
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(out) / "photos" / "archive_manifest.json"
    manifest = load(manifest_path) if manifest_path.is_file() else {}
    if manifest.get("query") == query and manifest.get("rows"):
        cached = [r for r in manifest["rows"] if Path(r["path"]).is_file()]
        if len(cached) >= min(wanted, len(manifest["rows"])):
            return cached
    results = searxng_images(query, out, limit=max(wanted * 3, 40))
    if not results:
        shorter = fallback_photo_query(query)
        if shorter:
            event(out, "searxng_fallback_query", query=query, fallback=shorter)
            results = searxng_images(shorter, out, limit=max(wanted * 3, 40))
    if not results:
        return []
    import requests as req
    rows = []
    seen = set()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    candidates = []
    for result in results:
        image_url = result.get("img_src") or result.get("thumbnail") or ""
        if image_url and image_url not in seen:
            seen.add(image_url)
            candidates.append(result)

    def get(result):
        try:
            response = req.get(result.get("img_src") or result.get("thumbnail"),
                               timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception:
            return None

    # The images were fetched one after another: on the Kailasa film the
    # 42 photographs took 82 s, all of it in front of the second
    # inventory round. They are fetched eight at a time and still
    # accepted in result order, so the same photographs get the same
    # names; at most seven fetches past the last one are thrown away.
    with ThreadPoolExecutor(max_workers=8) as pool:
        for start in range(0, len(candidates), 8):
            batch = candidates[start:start + 8]
            for result, blob in zip(batch, pool.map(get, batch)):
                if len(rows) >= wanted:
                    break
                row = _archive_photo(result, blob, directory, len(rows)) if blob else None
                if row:
                    rows.append(row)
            if len(rows) >= wanted:
                break
    save(manifest_path, {"query": query, "rows": rows})
    event(out, "archive_photos_fetched", query=query, count=len(rows))
    return rows


def _archive_query_done(out, query):
    """Whether this job already fetched archive photographs for this query."""
    manifest_path = Path(out) / "photos" / "archive_manifest.json"
    return manifest_path.is_file() and load(manifest_path).get("query") == query


def _archive_photo(result, blob, directory, index):
    """The photo row of one fetched image, None when it is no real photograph."""
    image_url = result.get("img_src") or result.get("thumbnail") or ""
    page_url = result.get("url") or ""
    target = directory / ("photo_%03d%s" % (index, Path(image_url.split("?")[0]).suffix or ".jpg"))
    if len(blob) < 20000:
        # A real archive photograph is larger than a placeholder.
        return None
    try:
        target.write_bytes(blob)
        with Image.open(target) as image:
            image.verify()
        with Image.open(target) as image:
            width, height = image.size
    except Exception:
        target.unlink(missing_ok=True)
        return None
    if width < 640 or height < 400:
        target.unlink(missing_ok=True)
        return None
    return {"id": "archive_photo_%03d" % index, "kind": "PHOTO",
            "path": str(target), "sha256": sha(target),
            "source_url": page_url, "image_url": image_url,
            "source_title": result.get("title", ""),
            "width": width, "height": height,
            "rights": "Archival photograph fetched from a public page; publication scope follows the user's approval"}

def download(url, out, prefer_height=1080):
    """Fetch one source video into the job's sources folder.

    The resolution order is 1080p, 720p, 480p. The hook shot is judged
    against a native 1080p rule, so the highest available resolution is
    tried first and the pipeline only falls back when the source does
    not publish one.

    A JavaScript runtime is required. Without it the YouTube extractor
    cannot resolve the player signature, the format list collapses and
    the download silently arrives at 360p even though a 1080p stream
    exists. That is measured, not assumed: the same request produced
    51.8 MB at 720p with the runtime and 18.6 MB at 360p without.
    """
    directory = Path(out) / "sources"
    directory.mkdir(exist_ok=True)
    search_dirs = [
        directory,
        Path(out).parent / "sources",
        Path(out) / "pilot_30s" / "sources",
        Path(out) / "sources",
        Path(out).parent / "03_materials" / "pilot_30s" / "sources",
    ]
    # Dynamically add project-level source dirs from environment or settings
    extra_source_dirs = os.environ.get("DOCUMENTARY_EXTRA_SOURCE_DIRS", "")
    if extra_source_dirs:
        for d in extra_source_dirs.split(";"):
            d = d.strip()
            if d:
                search_dirs.append(Path(d))
    for sdir in search_dirs:
        if sdir.is_dir():
            for cached in sdir.glob("*.json"):
                try:
                    meta = load(cached)
                    cached_path = Path(meta.get("path", ""))
                    if not cached_path.is_file():
                        sibling = cached.with_suffix(".mp4")
                        if sibling.is_file():
                            meta["path"] = str(sibling)
                            cached_path = sibling
                    if meta.get("url") == url and cached_path.is_file():
                        return meta
                except Exception:
                    pass
    if _site_of(url):
        # Only a short archive file is fetched whole, for its scene scan.
        # A long one is fetched as windows, and when those fail it is
        # lost rather than pulled whole: archive films run to gigabytes.
        meta = probe_source(url, out)
        if meta["duration"] > 90:
            raise FileNotFoundError("A long archive file is only fetched as windows")
        path, part = directory / (meta["id"] + ".mp4"), directory / (meta["id"] + ".part")
        _fetch_whole(meta["media_url"], part)
        try:
            run(["ffmpeg", "-v", "error", "-y", "-i", part, "-map", "0:v:0", "-c", "copy", "-an", path], 300)
        finally:
            part.unlink(missing_ok=True)
        meta = {**{k: meta[k] for k in ("id", "url", "title", "channel", "upload_date", "license", "rights")},
                "path": str(path), "sha256": sha(path), "probe": probe(path)}
        save(directory / (meta["id"] + ".json"), meta)
        return meta
    # DOWNLOAD-COST FIX: the production run pulled 74 sources totalling
    # 7.6 GB (median 60 MB each) and spent 411 s on the network, while the
    # footage actually used totals 891 s of screen time across all sources
    # (median 6.7 s per source). The runner accepts any source whose short
    # edge is >= 480 px, so 720p satisfies every quality rule in the
    # pipeline and cuts the transferred bytes to roughly a third.
    #
    # RESOLUTION ORDER: the best stream the source publishes, from
    # QUALITY_HEIGHTS downwards. The hook window is judged against a
    # native 1080p rule, so the best available stream is taken and the
    # pipeline only falls back when the source publishes nothing
    # larger.
    # A whole file another film already downloaded is taken from the
    # shared cache, with the metadata it was saved with.
    video_id = _youtube_id(url)
    shared_meta = yt_cache.get_json("full", [video_id, prefer_height], yt_cache.STORYBOARD_TTL) if video_id else None
    if shared_meta:
        entry = Path(shared_meta["cache"])
        path = directory / (video_id + entry.suffix)
        if yt_cache.take(entry, path):
            meta = {**{k: v for k, v in shared_meta.items() if k != "cache"}, "path": str(path), "probe": probe(path)}
            save(directory / (video_id + ".json"), meta)
            event(out, "source_cache_hit", id=video_id)
            return meta
    heights = _partial_heights(prefer_height)
    info = None
    path = None
    for height in heights:
        opts = _dl_opts(
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
            f"best[height<={height}][ext=mp4]/best[height<={height}]",
            directory / "%(id)s.%(ext)s")
        opts["max_filesize"] = 1024 * 1024 * 1024
        opts["nopart"] = False
        try:
            # Every rung selects from the one shared extraction.
            info, path = _ydl_download(url, opts, out)
        except Exception as exc:
            event(out, "source_download_failed", url=url, height=height,
                 error=type(exc).__name__, detail=str(exc)[:160])
            # A refusal is the same at every height.
            if _is_bot_check(exc) or yt_gate.throttled(exc) or isinstance(exc, yt_gate.YouTubeBlocked):
                break
            continue
        if path.is_file():
            break
        path = None
    if path is None or not path.is_file():
        raise FileNotFoundError("Downloader did not produce media")
    meta = {"id": info["id"], "path": str(path), "url": info.get("webpage_url", url),
            "title": info.get("title"), "channel": info.get("channel"), "upload_date": info.get("upload_date"),
            "license": info.get("license"), "sha256": sha(path), "probe": probe(path),
            "rights": "User-authorized YouTube reuse for this project; publication scope follows the user's approval"}
    save(directory / (info["id"] + ".json"), meta)
    entry = yt_cache.store(path, yt_cache.full_entry(info["id"], prefer_height, path.suffix.lstrip(".") or "mp4"))
    if entry:
        yt_cache.put_json("full", [info["id"], prefer_height],
                          {**{k: v for k, v in meta.items() if k not in ("path", "probe")}, "cache": str(entry)})
    return meta

# ---------------------------------------------------------------------------
# FOOTAGE SITES BESIDES YOUTUBE
#
# YouTube alone left whole sentences without a picture. Three public
# archives answer a keyword search without an API key and serve their
# files over plain HTTP: the Internet Archive, Wikimedia Commons (which
# also mirrors much US government footage, DVIDS and NTSB b-roll among
# it) and NASA. DVIDS itself refuses every request without a key, and
# NOAA has no video search API, so neither is searched.
#
# A site result is keyed by its canonical page URL, which is also its
# source_url and therefore its origin. Its file is fetched with ffmpeg
# straight from the URL, window by window, so a long archive film is
# never downloaded whole.
# ---------------------------------------------------------------------------

# Results taken from each archive per query. YouTube keeps its 25; the
# archives add a few each, so the selector sees a mixed list without the
# candidate count, and the downloads it picks from, multiplying.
SITE_SEARCH_LIMIT = 8

_SITE_HOSTS = {"archive.org": "archive", "commons.wikimedia.org": "commons", "images.nasa.gov": "nasa"}

def _site_of(url):
    """The archive a page URL belongs to, or None for YouTube and the rest."""
    return _SITE_HOSTS.get(urllib.parse.urlparse(str(url)).netloc.lower().removeprefix("www."))

def _site_id(url):
    # The id names files on disk and is the selector's handle, so it is
    # a short hash of the page URL: Commons titles carry characters a
    # file name cannot, and the same page always gets the same id.
    return "%s_%s" % (_site_of(url), digest(str(url))[:12])

def _http_json(url, params=None, timeout=15):
    import requests as req
    response = req.get(url, params=params, timeout=timeout,
                       headers={"User-Agent": "documentary-materials/1.0"})
    response.raise_for_status()
    return response.json()

_HTTP_INPUT = ["-user_agent", "documentary-materials/1.0", "-reconnect", 1,
               "-reconnect_on_http_error", "5xx", "-reconnect_delay_max", 30]

# upload.wikimedia.org refuses range seeking: measured, the third
# request to a file within ten seconds was answered 429 "Retry-After: 10"
# whatever the User-Agent, and one ffmpeg window cut needs four (header,
# cues at the end, header rest, seek point), so two of four Commons
# sources lost every window even with retries. A Commons file is
# therefore fetched in ONE request and cut locally; the probe keeps it
# to WHOLE_FILE_MAX_SECONDS. The robot policy also allows at most two
# concurrent downloads and 25 Mbps in total per client, which the slots
# and the per-slot rate enforce; the server itself delivered 10 to 27 MB/s.
_WHOLE_FILE_HOSTS = {"upload.wikimedia.org": threading.BoundedSemaphore(2)}
WHOLE_FILE_MAX_SECONDS = 600
WHOLE_FILE_BYTES_PER_SECOND = 25e6 / 8 / 2

def _fetch_whole(media_url, target):
    """One streamed GET of a whole archive file, waiting out a 429."""
    import requests as req
    host = urllib.parse.urlparse(media_url).netloc
    with _WHOLE_FILE_HOSTS.get(host, nullcontext()):
        for attempt in range(6):
            with req.get(media_url, stream=True, timeout=60,
                         headers={"User-Agent": "documentary-materials/1.0"}) as response:
                if response.status_code == 429 and attempt < 5:
                    time.sleep(float(response.headers.get("Retry-After") or 10) + 1)
                    continue
                response.raise_for_status()
                started, written = time.monotonic(), 0
                with open(target, "wb") as f:
                    for chunk in response.iter_content(1 << 20):
                        f.write(chunk)
                        written += len(chunk)
                        if host in _WHOLE_FILE_HOSTS:
                            time.sleep(max(0.0, written / WHOLE_FILE_BYTES_PER_SECOND - (time.monotonic() - started)))
                return

def _clock_seconds(value):
    """Seconds of an archive.org runtime such as "00:12:06", or None."""
    value = value[0] if isinstance(value, list) and value else value
    try:
        return float(sum(float(p) * 60 ** i for i, p in enumerate(reversed(str(value).split(":")))))
    except ValueError:
        return None

def _search_youtube(topic, limit=25, out=None):
    # The same query from another film, an expansion round or a later
    # sentence batch is answered from the shared cache.
    key = ["ytsearch", topic, limit]
    cached = yt_cache.get_json("search", key, yt_cache.SEARCH_TTL)
    if cached is not None:
        return cached
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True,
            "socket_timeout": 12, "retries": 1, **_yt_common()}

    def ask(query):
        def go():
            with yt_dlp.YoutubeDL(opts) as y:
                return y.extract_info("ytsearch%d:%s" % (limit, query), download=False)
        return yt_gate.call("search", go, out)
    data = ask(topic)
    # The fallback cuts a long query to six words. 1,010 of 1,015 short
    # answers came from queries of six words or fewer, for which it sent
    # the identical query again.
    short = " ".join(topic.split()[:6])
    if len(data.get("entries", [])) < 5 and short != " ".join(topic.split()):
        data = ask(short)
    rows = [{**{k: e.get(k) for k in ("id", "url", "title", "duration", "channel", "channel_id")}, "site": "youtube"}
            for e in data.get("entries", [])]
    yt_cache.put_json("search", key, rows)
    return rows

def _search_channel(channel_id, topic, limit=5, out=None):
    """A YouTube search inside one channel (the channel page's own search).

    Only videos are kept: the channel search also lists playlists, and an
    entry without a duration is a playlist or a live stream. A result
    has to share a word of four letters or more with the query, so a
    channel that has nothing on the subject gives nothing rather than its
    most popular unrelated upload.
    """
    url = "https://www.youtube.com/channel/%s/search?query=%s" % (channel_id, urllib.parse.quote(topic))
    key = ["channel", channel_id, topic, limit]
    data = yt_cache.get_json("search", key, yt_cache.SEARCH_TTL)
    if data is None:
        opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True,
                "socket_timeout": 12, "retries": 1, **_yt_common(), "playlistend": limit * 2}

        def go():
            with yt_dlp.YoutubeDL(opts) as y:
                return y.extract_info(url, download=False)
        found = yt_gate.call("channel_search", go, out)
        data = {"entries": [{k: e.get(k) for k in ("id", "title", "duration", "channel")}
                            for e in found.get("entries") or []]}
        yt_cache.put_json("search", key, data)
    words = {w for w in re.findall(r"\w+", topic.casefold()) if len(w) >= 4}
    rows = []
    for e in data.get("entries") or []:
        if not e.get("duration") or not words & set(re.findall(r"\w+", str(e.get("title") or "").casefold())):
            continue
        rows.append({**{k: e.get(k) for k in ("id", "title", "duration", "channel")},
                     "url": "https://www.youtube.com/watch?v=" + e["id"], "site": "youtube", "priority_channel": True,
                     "channel_id": channel_id})
    return rows[:limit]

def _search_archive(topic):
    # Words only: the query is Lucene syntax, and a stray quote or colon
    # from the query writer is a syntax error. The TV news archive is
    # left out because its files are private, and the "youtube-" items
    # because they are copies of YouTube videos the YouTube search finds.
    words = " ".join(re.findall(r"\w+", topic))
    data = _http_json("https://archive.org/advancedsearch.php", {
        "q": "(%s) AND mediatype:movies AND -collection:tvarchive AND -identifier:youtube-*" % words,
        "fl[]": ["identifier", "title", "creator", "runtime"], "rows": SITE_SEARCH_LIMIT, "output": "json"})
    rows = []
    for doc in data["response"]["docs"]:
        url = "https://archive.org/details/" + doc["identifier"]
        rows.append({"id": _site_id(url), "url": url, "title": doc.get("title"),
                     "duration": _clock_seconds(doc["runtime"]) if doc.get("runtime") else None,
                     "channel": "Internet Archive", "site": "archive"})
    return rows

def _search_commons(topic):
    data = _http_json("https://commons.wikimedia.org/w/api.php", {
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": "filetype:video " + topic, "gsrlimit": SITE_SEARCH_LIMIT,
        "prop": "videoinfo", "viprop": "url|size"})
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    rows = []
    for page in pages:
        info = (page.get("videoinfo") or [{}])[0]
        if info.get("descriptionurl"):
            rows.append({"id": _site_id(info["descriptionurl"]), "url": info["descriptionurl"],
                         "title": page["title"].removeprefix("File:"), "duration": info.get("duration"),
                         "channel": "Wikimedia Commons", "site": "commons"})
    return rows

def _search_nasa(topic):
    data = _http_json("https://images-api.nasa.gov/search",
                      {"q": topic, "media_type": "video", "page_size": SITE_SEARCH_LIMIT})
    rows = []
    for item in data["collection"]["items"][:SITE_SEARCH_LIMIT]:
        about = item["data"][0]
        url = "https://images.nasa.gov/details/" + urllib.parse.quote(about["nasa_id"])
        rows.append({"id": _site_id(url), "url": url, "title": about.get("title"), "duration": None,
                     "channel": "NASA " + str(about.get("center") or ""), "site": "nasa"})
    return rows

# Commons first among the archives: its matches are titled files, often
# 1080p or 4K government footage, while the Internet Archive matches any
# word of a long description.
_SEARCHERS = {"youtube": _search_youtube, "commons": _search_commons,
              "archive": _search_archive, "nasa": _search_nasa}

# YouTube channel ids a film may take footage from; None takes every
# channel. Set by prepare() from the profile ("bbc_only"), so every search
# of the run keeps to it. With "logo_free_fallback" the shot queue's own
# searches (relax_channels) also take other channels: such a video gets a
# "<id>.nonbbc" marker in the run's sources folder, and its shots are
# reviewed with "any logo is a blocking defect" (is_non_bbc).
ALLOWED_CHANNELS = None
RELAXED = False
_FALLBACK = False
_MARKS = None


# Channels that sell their footage and stamp a licensing notice over it
# (the user's rule, 2026-11-01): never a candidate.
LICENSE_SELLERS = re.compile(r"storm ?chasing ?video|\bscv\b|pond5|shutterstock|storyblocks|videoblocks|getty ?images|"
                             r"alamy|viralhog|jukin|newsflare|to licen[cs]e|for licensing", re.I)


def _seller(c):
    return bool(LICENSE_SELLERS.search("%s %s" % (c.get("channel") or "", c.get("title") or "")))


def _allowed(result):
    result = {**result, "candidates": [c for c in result["candidates"] if not _seller(c)]}
    if ALLOWED_CHANNELS is None:
        return result
    keep = []
    for c in result["candidates"]:
        if c.get("channel_id") in ALLOWED_CHANNELS:
            keep.append(c)
        elif RELAXED and c.get("site") == "youtube" and c.get("id"):
            (_MARKS / (c["id"] + ".nonbbc")).touch()
            keep.append(c)
    return {**result, "candidates": keep}


def restrict_channels(production, out):
    global ALLOWED_CHANNELS, RELAXED, _FALLBACK, _MARKS
    ALLOWED_CHANNELS = set(production["priority_channel_ids"]) if production.get("bbc_only") else None
    _FALLBACK = bool(production.get("logo_free_fallback"))
    _MARKS = Path(out) / "sources"
    _MARKS.mkdir(parents=True, exist_ok=True)
    # "nonbbc_from_start": other channels' footage joins the first pool too,
    # under the same marker and logo rule, instead of only the shot queue's.
    RELAXED = ALLOWED_CHANNELS is not None and _FALLBACK and bool(production.get("nonbbc_from_start"))


def relax_channels():
    """From here on, a search may also take logo-free footage of other channels."""
    global RELAXED
    RELAXED = ALLOWED_CHANNELS is not None and _FALLBACK


def is_non_bbc(path):
    """True when a source file comes from a video marked by a relaxed search."""
    path = Path(path)
    vid = path.name.split("_windows")[0].rsplit(".", 1)[0]
    return (path.parent / (vid + ".nonbbc")).exists()


def search(topic, out, archive=False, channels=(), sites=None, limit=25, channel_take=5):
    """Candidates for one query, from every site, priority channels first.

    channels is a list of (name, channel id) searched before the rest
    (the wildlife profile's BBC channels); sites limits the searchers and
    limit the YouTube result count. The defaults are the search as it
    always was, with the same cache identity.
    """
    target = Path(out) / "source_search.json"
    searchers = {site: f for site, f in _SEARCHERS.items() if sites is None or site in sites}
    key = {"topic": topic, "archive": archive, "sites": list(searchers)}
    if channels or limit != 25:
        key.update(channels=[c for _, c in channels], limit=limit, channel_take=channel_take)
    # A channel-restricted film (bbc_only) keeps only YouTube rows
    # (_allowed): an archive row has no channel, so its search was a
    # request whose answer was always dropped (426 in the PAR runs).
    skipped = [site for site in searchers if ALLOWED_CHANNELS is not None and site != "youtube"]
    if skipped:
        key["skipped"] = skipped
        searchers = {site: f for site, f in searchers.items() if site not in skipped}
    identity = digest(key)
    if target.exists() and load(target).get("identity") == identity:
        return _allowed(load(target))
    film = _film_of(out)
    with ThreadPoolExecutor(max_workers=max(1, len(searchers) + len(channels))) as pool:
        futures = {site: pool.submit(searcher, topic, limit, film) if site == "youtube" else pool.submit(searcher, topic)
                   for site, searcher in searchers.items()}
        channel_futures = {name: pool.submit(_search_channel, cid, topic, channel_take, film) for name, cid in channels}
    found, sites = {}, {}
    for site, future in futures.items():
        try:
            found[site] = future.result()
            sites[site] = len(found[site])
        except Exception as exc:
            # One archive being down must not cost the others' results.
            if site == "youtube" and not channels:
                raise
            found[site], sites[site] = [], "%s: %s" % (type(exc).__name__, str(exc)[:120])
    for site in skipped:
        sites[site] = "skipped: channel-restricted profile"
    priority = []
    for name, future in channel_futures.items():
        try:
            priority.append(future.result())
            sites["channel:" + name] = len(priority[-1])
        except Exception as exc:
            sites["channel:" + name] = "%s: %s" % (type(exc).__name__, str(exc)[:120])
    # Round robin over the sites, so the first results of a query, which
    # are what the shot search takes, are not all from one site. The
    # priority channels come before all of them, round robin as well.
    candidates = [row for rows in (priority, list(found.values())) for rank in zip_longest(*rows) for row in rank if row]
    if channels:
        # A channel hit is often the general search's hit too.
        seen = set()
        candidates = [c for c in candidates if not (c["id"] in seen or seen.add(c["id"]))]
    result = {"identity": identity, "query": topic, "sites": sites, "candidates": candidates}
    save(target, result)
    return _allowed(result)

def pre_filter_quality(row, out):
    """ADIM 2: Deterministik kalite ön-filtresi — LLM'e göndermeden önce
    düşük çözünürlüklü, siyah/bozuk frame'li asset'leri ele.
    Returns (pass: bool, reason: str)"""
    from .io import probe as _probe
    path = row.get("path", "")
    if not Path(path).is_file():
        return False, "file_not_found"

    # 1. Video çözünürlük kontrolü
    if row.get("kind") == "VIDEO":
        try:
            info = _probe(path)
            stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
            width = int(stream.get("width", 0))
            height = int(stream.get("height", 0))
            min_dim = min(width, height) if width and height else 0
            if min_dim > 0 and min_dim < 240:
                return False, f"resolution_too_low_{width}x{height}"
        except Exception:
            pass  # probe failure → let LLM decide

    # 2. Statik resim boyut kontrolü (çok küçük dosyalar)
    if row.get("kind") in ("PHOTO", "2D"):
        try:
            fsize = Path(path).stat().st_size
            if fsize < 5000:  # <5KB image is likely corrupt/placeholder
                return False, f"file_too_small_{fsize}B"
        except Exception:
            pass

    # 3. Video siyah frame kontrolü (ilk frame'i kontrol et)
    if row.get("kind") == "VIDEO":
        try:
            start = float(row.get("start", 0))
            proc = resources.media_run(
                ["ffmpeg", "-v", "error", "-ss", str(start), "-i", path,
                 "-frames:v", "1", "-vf", "blackdetect=d=0:pix_th=0.10",
                 "-f", "null", "-"],
                capture_output=True, text=True, timeout=10
            )
            # Eğer ilk frame tamamen siyahsa, skip et
            if "black_start:0" in (proc.stderr or "") and float(row.get("end", 0)) - start < 3:
                return False, "all_black_short_segment"
        except Exception:
            pass  # timeout/error → let LLM decide

    return True, "ok"

def scene_shots(meta, out):
    stream=next((s for s in meta.get("probe",{}).get("streams",[]) if s.get("codec_type")=="video"),{})
    dimensions={"native_width":int(stream.get("width") or 0),"native_height":int(stream.get("height") or 0)}
    """Detect source shots; never loop, slow down or cross their context boundaries."""
    target = Path(out) / "sources" / (meta["id"] + "_shots.json")
    if target.exists() and load(target).get("source_sha256") == meta["sha256"]:
        return [{**row,**dimensions} for row in load(target)["rows"]]
    path = meta["path"]
    duration = float(meta["probe"]["format"]["duration"])
    # Keep the filter portable across the bundled FFmpeg builds; scene boundaries
    # are only candidate shot bounds and do not require variable-rate output.
    # Full-source scene detection is useful, but it must not hold a worker for
    # many minutes on a slow 4K/archival file.  Keep a short, explicit budget;
    # on timeout use deterministic 14-second windows so material production can
    # continue and the next admission round can add sources if capacity is low.
    scene_timeout = int(os.environ.get("DOCUMENTARY_SCENE_TIMEOUT", "15"))
    if duration > 90:
        cuts = [float(t) for t in range(0, max(1, math.ceil(duration)), 14)] + [duration]
    else:
        try:
            log = run(["ffmpeg", "-hide_banner", "-i", path, "-an", "-vf", "scale=320:-1,select='gt(scene,0.35)',showinfo", "-f", "null", "-"], scene_timeout).stderr.decode(errors="replace")
            cuts = [0.] + [float(t) for t in re.findall(r"pts_time:([\d.]+)", log)] + [duration]
        except Exception as exc:
            event(out, "scene_scan_fallback", id=meta["id"], error=type(exc).__name__, timeout=scene_timeout)
            cuts = [float(t) for t in range(0, max(1, math.ceil(duration)), 14)] + [duration]
    cuts = sorted(set(cuts))
    rows = []
    for a, b in zip(cuts, cuts[1:]):
        # Long unchanged interview frames are split for audit, not assumed to be b-roll.
        for i in range(max(1, math.ceil((b - a) / 14))):
            start = a + i * 14
            end = min(start + 14, b)
            if end - start < 2:
                continue
            rows.append({"id": f'{meta["id"]}_{len(rows):03}', "kind": "VIDEO", "path": path,
                          "start": round(start, 3), "end": round(end, 3), "sha256": meta["sha256"],
                          "source_url": meta["url"], "source_title": meta["title"], "rights": meta["rights"],**dimensions})
    save(target, {"source_sha256": meta["sha256"], "rows": rows})
    return rows

def probe_source(url, out):
    """Read a video's metadata without downloading its body.

    The scene scan of a long source does not need the file: it splits
    the timeline into deterministic 14 second windows anyway. Only a
    source of 90 seconds or less is scene-scanned, and those are small
    enough to fetch whole.

    The metadata gives the duration and the resolution, which is what
    the window planner needs to decide which parts of the source the
    film will actually use.
    """
    directory = Path(out) / "sources"
    directory.mkdir(exist_ok=True)
    if _site_of(url):
        return _probe_site(url)
    # A video is probed once per PROBE_TTL for every film: the PAR reruns
    # probed 147 ids a second or third time (expansion rounds re-probe the
    # sources they hold), and 80 ids were probed by two films or runs.
    video_id = _youtube_id(url)
    cached = yt_cache.get_json("probe", video_id, yt_cache.PROBE_TTL) if video_id else None
    if cached is not None:
        if cached.get("error"):
            raise yt_dlp.utils.DownloadError(cached["error"])
        return cached
    try:
        info = _youtube_info(url, out)
    except Exception as exc:
        # Only what the video itself says (gone, private, age-gated) is
        # kept; a refusal or a timeout is asked again.
        if video_id and any(k in str(exc) for k in _GONE) and not yt_gate.throttled(exc):
            yt_cache.put_json("probe", video_id, {"error": str(exc)[:300]})
        raise
    if not info:
        raise FileNotFoundError("Source metadata could not be read")
    formats = [f for f in (info.get("formats") or [])
               if f.get("vcodec") not in (None, "none") and f.get("height")]
    mp4s = [f for f in formats if f.get("ext") == "mp4" and f.get("protocol") == "https"]
    best = max(mp4s, key=lambda f: f.get("height") or 0) if mp4s else None
    duration = float(info.get("duration") or 0)
    height = int((best or {}).get("height") or info.get("height") or 0)
    width = int((best or {}).get("width") or info.get("width") or 0)
    payload = {"id": info.get("id"), "url": info.get("webpage_url", url),
               "title": info.get("title"), "channel": info.get("channel"),
               "upload_date": info.get("upload_date"),
               "license": info.get("license"), "duration": duration,
               "height": height, "width": width,
               "rights": "User-authorized YouTube reuse for this project; publication scope follows the user's approval",
               # The same extraction already lists the storyboard images,
               # so judging the whole video costs no second extractor call.
               "storyboard": _storyboard_format(info)}
    if video_id:
        yt_cache.put_json("probe", video_id, payload)
    return payload

def _probe_site(url):
    """The metadata of an archive page and the one file its windows are cut from.

    The file is the largest one, up to the 4K the film can use, whose
    picture ffmpeg can copy into an mp4 untouched: H.264 or MPEG-4 on
    the Internet Archive, VP9, H.264 or AV1 on Commons, whose Theora and
    VP8 originals an mp4 cannot carry but whose VP9 transcodes it can.
    The duration and the size are read from the file itself by ffprobe,
    because the page metadata is often missing or rounded.

    Commons stops at 1080p: its robot policy caps an automated client
    at 25 Mbps, and a 4K original runs at about that rate on its own.
    Its file is not probed either, because every request to it counts
    against the 429 limit; the API's own duration and sizes are used.
    """
    site = _site_of(url)
    path = urllib.parse.urlparse(url).path
    files = []
    if site == "archive":
        identifier = path.split("/details/", 1)[1].split("/")[0]
        item = _http_json("https://archive.org/metadata/" + identifier)
        about = item.get("metadata") or {}
        title, channel, license_ = about.get("title"), about.get("creator") or "Internet Archive", about.get("licenseurl")
        files = sorted(((int(float(f.get("height") or 0)), "https://archive.org/download/%s/%s" % (identifier, urllib.parse.quote(f["name"])))
                        for f in item.get("files") or []
                        if not f.get("private") and f["name"].lower().endswith((".mp4", ".m4v", ".mov"))
                        and any(c in str(f.get("format", "")).lower() for c in ("h.264", "mpeg4"))), reverse=True)
    elif site == "commons":
        page = urllib.parse.unquote(path.split("/wiki/", 1)[1])
        data = _http_json("https://commons.wikimedia.org/w/api.php", {
            "action": "query", "format": "json", "titles": page,
            "prop": "videoinfo", "viprop": "size|derivatives|extmetadata"})
        info = (next(iter(data["query"]["pages"].values())).get("videoinfo") or [{}])[0]
        title, channel = page.removeprefix("File:"), "Wikimedia Commons"
        license_ = ((info.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value")
        if float(info.get("duration") or 0) > WHOLE_FILE_MAX_SECONDS:
            raise FileNotFoundError("A Commons file is fetched whole, and this one is too long: " + url)
        files = sorted(((int(d.get("height") or 0), d["src"], int(d.get("width") or 0)) for d in info.get("derivatives") or []
                        if any(c in d.get("type", "") for c in ("vp9", "avc1", "av01"))), reverse=True)
    else:
        nasa_id = urllib.parse.unquote(path.split("/details/", 1)[1])
        item = _http_json("https://images-api.nasa.gov/search", {"nasa_id": nasa_id})["collection"]["items"][0]
        title, channel = item["data"][0].get("title"), "NASA " + str(item["data"][0].get("center") or "")
        license_ = "NASA media usage guidelines"
        # NASA names its renditions instead of sizing them; "orig" is the
        # master, which is H.264 when its name ends in .mp4.
        renditions = {href.rsplit("~", 1)[-1]: href.replace("http://", "https://", 1)
                      for href in _http_json(item["href"]) if "~" in href}
        files = [(0, renditions[name]) for name in ("orig.mp4", "large.mp4", "medium.mp4") if name in renditions]
    # A file taller than the film can use costs bytes and decoding time
    # for nothing; the next one down is the same picture.
    files = [f for f in files if f[0] <= (1080 if site == "commons" else QUALITY_HEIGHTS[0])]
    if not files:
        raise FileNotFoundError("No video file an mp4 can carry on " + url)
    media_url = files[0][1]
    if site == "commons":
        duration, height, width = float(info.get("duration") or 0), files[0][0], files[0][2]
    else:
        found = json.loads(run(["ffprobe", "-v", "error", *_HTTP_INPUT, "-show_format", "-show_streams",
                                "-of", "json", media_url], 60).stdout)
        stream = next(s for s in found.get("streams", []) if s.get("codec_type") == "video")
        duration = float((found.get("format") or {}).get("duration") or 0)
        height, width = int(stream.get("height") or 0), int(stream.get("width") or 0)
    return {"id": _site_id(url), "url": url, "media_url": media_url, "site": site,
            "title": title, "channel": channel, "upload_date": None, "license": license_,
            "duration": duration, "height": height, "width": width,
            "rights": "%s file, license %s; publication scope follows the user's approval" % (channel, license_ or "not stated")}

def plan_windows(meta, count, duration_hint=None):
    """Choose which parts of a source the film is likely to use.

    The choice is measured, not guessed. The delivered film made 60
    camera cuts from 46 sources, and every one of them landed in the
    middle band of its source: 56 of the 60 sat between 45 and 51
    percent of the source duration, and the rest were in the 22 to 29
    percent band. The absolute start seconds were 602.0 of 1206.3,
    1414.0 of 2834.3, 434.0 of 871.9, 1372.0 of 2755.3, 322.0 of
    653.2 and 1400.0 of 2819.3.

    The reason is the inventory order. The scene scan of a long source
    cuts it into deterministic 14 second windows, and the shortlist
    walks each source's windows in a bisect order, so the middle
    window of every source is classified first. The film then uses
    what was classified.

    So the window is placed on the middle of the source. Fetching the
    first two minutes of a 47 minute source, which is what this did
    before, spends the whole request on footage the film never cuts.

    The window is WIDE rather than many. The film cuts its footage
    from a narrow band: the median distance between the cut and the
    middle of its source is 5.4 seconds, and 57 of the 60 cuts sit
    within 30 seconds of the middle. A single 32 second window covers
    57 of the 60 cuts, and the two narrow windows it replaced covered
    54 of the 60, because the second narrow window was a quarter of
    the way in and the film almost never cut there. One wide window
    therefore covers more of the film than the two narrow ones, and it
    costs one request instead of two.
    """
    duration = float(duration_hint or meta.get("duration") or 0)
    if duration <= 0:
        return []
    count = max(1, int(count))
    # A recording may be cut up to three times, so it can need more
    # than one window. How many is the caller's decision.
    wanted = min(RANGE_MAX_WINDOWS, count)
    # The scene window is 14 seconds, and the excerpt is cut out of one
    # scene window, so the fetch has to cover the scene window and not
    # just the excerpt. The cut is taken from the first seconds of the
    # window in 37 of the 57 delivered cases, so the window starts a
    # little before the scene window does.
    span = min(RANGE_MAX_SECONDS, max(RANGE_MIN_SECONDS, SCENE_WINDOW_SECONDS + 6.0, RANGE_WIDE_SECONDS))
    windows = []
    # One window gives a recording one cut: two cuts need 30 seconds
    # between them and a window is 32 seconds. So the windows of one
    # source sit at least a window plus the gap apart, spread over the
    # 15-85 percent band, which skips title cards and end credits. The
    # middle-only window above was measured on where the old film cut,
    # and the old film only cut there because only the middle was fetched.
    band_start, band_end = duration * 0.15, duration * 0.85
    step = span + 2 * RANGE_PADDING_SECONDS + MIN_SAME_ORIGIN_GAP_SECONDS
    wanted = min(wanted, 1 + int(max(0.0, band_end - band_start - span) // step))
    if wanted == 1:
        windows.append((duration * 0.5 - span / 2, duration * 0.5 + span / 2))
    else:
        first = band_start + span / 2
        spacing = (band_end - band_start - span) / (wanted - 1)
        for i in range(wanted):
            mid = first + i * spacing
            windows.append((mid - span / 2, mid + span / 2))
    # A window that falls outside the source is not a window.
    windows = [(max(0.0, a), min(duration, b)) for a, b in windows]
    windows = [(a, b) for a, b in windows if b - a >= 1.0]
    return [_range_windows(a, b) for a, b in windows]

# ---------------------------------------------------------------------------
# STORYBOARD JUDGE: look at the whole video before fetching any of it
#
# YouTube serves a storyboard for the seek bar: JPEG grids of small
# frames, one frame about every 10 s over the whole video. yt-dlp lists
# them as the formats sb0..sb3, and the probe's extraction already has
# their URLs. sb1 (160x90, 5x5 per sheet) is read here: a 54 minute
# video is 13 sheets, 0.57 MB and about 1.4 s; a 112 minute one is 27
# sheets, 1.2 MB and about 1.9 s, six at a time. sb0 (320x180) is three
# times the bytes and the time for a picture Flash does not need to tell
# an interview from footage.
#
# Flash sees the whole storyboard, labelled with frame numbers and
# times, and names the stretches of clean B-roll. The windows are then
# placed on those stretches instead of blindly over the 15-85 percent
# band. Measured on five Gobekli Tepe sources (a NOVA film, three
# documentaries, an excavation walk-through, a podcast), three windows
# each, the 45 contact frames of the blind windows were 19 B-roll, 24
# talking heads and 2 title cards; the 36 frames of the storyboard
# windows were 31 B-roll and 5 talking heads. Windows with at least two
# B-roll frames of three: 6 of 15 blind, 12 of 12 placed. The podcast was
# rejected from its storyboard and fetched not at all; the other four
# were fetched in 279 MB instead of 389 MB. Flash answered in 8 to 14 s
# per video.
#
# Through prepare() on a 17 source Gobekli Tepe selection, four download
# slots: the fetch took 143 s instead of 182 s, the same 1.23 GB (clean
# footage moves, so it compresses worse than a talking head) bought 46
# windows instead of 52, and the windows whose three contact frames were
# all B-roll went from 33 of 52 to 36 of 46; windows with a talking
# head from 6 to 3. A 240p lecture that was one talking head for 25
# minutes was rejected without a byte of video.
#
# A source with no storyboard (the archives, NASA) or whose storyboard
# or judgement fails is fetched the old way, from plan_windows. The
# windows land in the same files with the same map, so everything after
# the fetch, describe_group included, is unchanged.
# ---------------------------------------------------------------------------

STORYBOARD = os.environ.get("DOCUMENTARY_STORYBOARD", "1") != "0"
# A sheet sent to Flash is 8 x 6 frames of 160x90 with a label line, so
# it is 1280 wide and fits the 1280x720 image payload without being
# scaled down again. A long video is thinned to six sheets: one frame
# per 25 s on a two hour video still shows every sequence of footage.
STORYBOARD_MIN_WIDTH = 120
STORYBOARD_SHEET = (8, 6)
STORYBOARD_MAX_FRAMES = 288
STORYBOARD_LABEL = 18

# The judge waits on Flash, not on the line, so prepare runs more
# sources at a time than it lets download; these slots keep the number
# of ffmpeg window fetches at the old concurrency.
_DOWNLOAD_SLOTS = threading.BoundedSemaphore(max(1, int(os.environ.get("DOCUMENTARY_DOWNLOAD_CONCURRENCY", "16"))))

_STORYBOARD_PROMPT = (
    'These images are the storyboard of ONE video: low resolution frames in time order, each labelled "#N m:ss" with its '
    'frame number and time in the video. A documentary will cut short B-roll excerpts from this video. '
    'Judge the whole video and find the stretches of clean B-roll: real moving camera footage of places, objects, '
    'landscapes, excavation, artefacts or events; reconstruction animations, CGI and maps of the subject count too. '
    'NOT clean: a person talking to the camera or an interview '
    '(talking heads), presenters, podcasts or studio shots, burned-in subtitles that transcribe speech, title cards, '
    'end credits, black or text-only screens, slides, screen recordings. Logos, watermarks and channel bugs are fine '
    'and are never a problem. ' + LICENSE_OVERLAY_RULE + 'A range is consecutive frame numbers that are ALL clean B-roll; list every such range '
    'of 2 or more frames, best first. JSON {description:string,usable:boolean,problems:[string],keywords:[string],'
    'ranges:[{first:integer,last:integer,content:string}]}. usable is false when the video has no clean B-roll range. '
    'Video title: ')


def _storyboard_format(info):
    """The smallest storyboard that is still legible, or None."""
    boards = [f for f in info.get("formats") or [] if str(f.get("format_id", "")).startswith("sb")
              and f.get("fragments") and f.get("fps") and f.get("columns") and f.get("rows")
              and (f.get("width") or 0) >= STORYBOARD_MIN_WIDTH]
    if not boards or not info.get("duration"):
        return None
    f = min(boards, key=lambda f: f["width"])
    return {"width": f["width"], "height": f["height"], "columns": f["columns"], "rows": f["rows"],
            "interval": 1 / f["fps"], "frames": math.ceil(float(info["duration"]) * f["fps"]),
            "sheets": [x["url"] for x in f["fragments"]]}


def _storyboard_frames(board, video_id=None, out=None):
    """(second, image) for every storyboard frame, thinned to the cap."""
    def get(item):
        index, url = item
        blob = yt_cache.get_sheet(video_id, index) if video_id else None
        if blob is None:
            yt_gate.wait_clear(out)
            with urllib.request.urlopen(url, timeout=20) as r:
                blob = r.read()
            if video_id:
                yt_cache.put_sheet(video_id, index, blob)
        return blob
    with ThreadPoolExecutor(max_workers=6) as pool:
        blobs = list(pool.map(get, enumerate(board["sheets"])))
    w, h, cols = board["width"], board["height"], board["columns"]
    per = cols * board["rows"]
    frames = []
    for k, blob in enumerate(blobs):
        with Image.open(BytesIO(blob)) as sheet:
            sheet = sheet.convert("RGB")
            # The last sheet is only partly filled; its blank cells lie
            # past the frame count.
            for j in range(min(per, board["frames"] - k * per)):
                x, y = (j % cols) * w, (j // cols) * h
                frames.append(((k * per + j) * board["interval"], sheet.crop((x, y, x + w, y + h))))
    if len(frames) > STORYBOARD_MAX_FRAMES:
        step = len(frames) / STORYBOARD_MAX_FRAMES
        frames = [frames[int(i * step)] for i in range(STORYBOARD_MAX_FRAMES)]
    return frames


def _storyboard_sheets(frames, folder, w, h):
    cols, rows = STORYBOARD_SHEET
    font = ImageFont.truetype(FONT, 14)
    paths = []
    for s in range(0, len(frames), cols * rows):
        chunk = frames[s:s + cols * rows]
        canvas = Image.new("RGB", (cols * w, math.ceil(len(chunk) / cols) * (h + STORYBOARD_LABEL)), "#e9ecef")
        d = ImageDraw.Draw(canvas)
        for i, (sec, im) in enumerate(chunk):
            x, y = (i % cols) * w, (i // cols) * (h + STORYBOARD_LABEL)
            d.text((x + 2, y + 1), "#%d %d:%02d" % (s + i, sec // 60, sec % 60), font=font, fill="#14212f")
            canvas.paste(im.resize((w, h)), (x, y + STORYBOARD_LABEL))
        path = Path(folder) / ("storyboard_%02d.jpg" % (s // (cols * rows)))
        canvas.save(path, quality=88)
        paths.append(str(path))
    return paths


def judge_storyboard(meta, out):
    """Flash's verdict on a whole YouTube video from its storyboard.

    Returns {description, usable, problems, keywords, ranges:[[a, b]]}
    in source seconds, or None when there is no storyboard or it could
    not be read or judged. The verdict is kept beside the windows as
    <id>.storyboard.json, so a rerun places the same windows and finds
    its window files in the cache; recovery also takes the name as a
    source it has already seen.
    """
    board = meta.get("storyboard")
    if not board:
        return None
    target = Path(out) / "sources" / ("%s.storyboard.json" % meta["id"])
    if target.is_file():
        cached = load(target)
        if cached.get("url") == meta.get("url"):
            return cached
    folder = Path(out) / "storyboards" / str(meta["id"])
    folder.mkdir(parents=True, exist_ok=True)
    try:
        frames = _storyboard_frames(board, meta.get("id"), out)
        sheets = _storyboard_sheets(frames, folder, board["width"], board["height"])
        result = api("flash", _STORYBOARD_PROMPT + str(meta.get("title")), folder / "flash.json", sheets,
                     tokens=2500, timeout=60, hedge_override=30, max_attempts_override=2,
                     deadline=time.monotonic() + 90)["data"]
    except Exception as exc:
        event(out, "storyboard_unavailable", id=meta["id"], error=type(exc).__name__, detail=str(exc)[-200:])
        return None
    times = [s for s, _ in frames]
    gap = times[1] - times[0] if len(times) > 1 else board["interval"]
    duration = float(meta.get("duration") or 0)
    ranges = []
    for r in result.get("ranges") or []:
        try:
            a, b = int(r.get("first")), int(r.get("last"))
        except (TypeError, ValueError):
            continue
        if 0 <= a <= b < len(times):
            # A frame stands for the stretch up to the next frame.
            ranges.append([round(times[a], 1), round(min(duration, times[b] + gap), 1)])
    verdict = {"url": meta.get("url"), **{k: result.get(k) for k in ("description", "usable", "problems", "keywords")},
               "ranges": ranges, "frames": len(frames), "receipt": str(folder / "flash.json")}
    save(target, verdict)
    event(out, "storyboard_judged", id=meta["id"], usable=verdict["usable"], ranges=len(ranges), frames=len(frames))
    return verdict


def storyboard_windows(ranges, duration, count):
    """Windows of the usual width, centred on the clean ranges, best first.

    A long range gives several windows, spaced as plan_windows spaces
    them (a window, its padding and the same-origin gap apart), so every
    window can give its own cut.
    """
    span = RANGE_WIDE_SECONDS
    step = span + 2 * RANGE_PADDING_SECONDS + MIN_SAME_ORIGIN_GAP_SECONDS
    centres = []
    for a, b in ranges:
        if b - a <= span:
            centres.append((a + b) / 2)
        else:
            centres.extend(a + span / 2 + i * step for i in range(1 + int((b - a - span) // step)))
    chosen = []
    for c in centres:
        if len(chosen) < min(count, RANGE_MAX_WINDOWS) and all(abs(c - x) >= step for x in chosen):
            chosen.append(c)
    windows = []
    for c in sorted(chosen):
        a = min(max(0.0, c - span / 2), max(0.0, duration - span))
        windows.append(_range_windows(a, min(duration, a + span)))
    return windows


# ---------------------------------------------------------------------------
# PINPOINT: let Flash watch a YouTube video for the film's own sentences
#
# Gemini reads a YouTube video from its URL. One Flash call per candidate
# gets the narration sentences and answers which seconds of the video show
# what each sentence describes, so only those seconds are fetched and each
# window arrives knowing the sentence it was found for. The storyboard
# judge only tells B-roll from talking heads: its windows then waited for
# a Flash describe of their contact frames, and the selector still had to
# guess which sentence they fit.
#
# Measured on six Pantanal sources with the 24 sentences of one film in
# one prompt: 9 to 29 s per call for videos up to 30 minutes, 82 s for a
# 74 minute one. Of the matches with confidence >= 0.8 that ended inside
# the video, 75% were right, 19% partly right (the moment crosses a cut)
# and 6% wrong; repeated calls agreed within 2 s. The wrong ones were an
# end card in the last seconds and times past the end of the video, so
# both are filtered here. Two-minute clips were the weakest.
#
# A source the pinpoint cannot read, or in which it finds nothing, goes
# the storyboard way, and one without a storyboard the plan_windows way,
# as before. Archive, Commons and NASA files are never sent: the model
# reads only YouTube URLs.
# ---------------------------------------------------------------------------

PINPOINT = os.environ.get("DOCUMENTARY_PINPOINT", "0") != "0"  # gateway cannot watch YouTube (HTTP 400): off unless =1
# Below 0.8 the measured matches were mostly guesses from the title.
PINPOINT_MIN_CONFIDENCE = 0.8
# The wrong matches clustered on the end card of the last ~10 s.
PINPOINT_END_SECONDS = 10.0
# The 74 minute video took 82 s; the ceiling leaves room for longer ones
# without holding a worker longer than the storyboard fallback is worth.
PINPOINT_TIMEOUT_SECONDS = 150
# A long video is not pinpointed: a 74-minute one took 82 s, and on
# TOPIC_2 videos of one to two hours came back HTTP 400 after 66 s or
# held a Flash channel for the whole 150 s timeout, so the short videos
# queued behind them. Those go the storyboard way.
PINPOINT_MAX_VIDEO_SECONDS = 45 * 60
# Watching a video costs its account tens of thousands of input tokens
# (51 007 for one), and the TOPIC_2 runs pinpointed ~45 videos each:
# several accounts were blocked for days on quota and the gateway stalled
# for 7 minutes. The first sources of a round (the search ranks them) are
# pinpointed; the rest take the storyboard.
PINPOINT_MAX_SOURCES = 24

_PINPOINT_PROMPT = (
    "You are given ONE YouTube video. A documentary needs short B-roll cuts from it. Below are numbered narration "
    "sentences. For each sentence, find the moments in THIS video whose PICTURE shows what the sentence describes "
    "(the subject, action, place or condition). Only clean footage: no talking heads, presenters, interviews, title "
    "cards, text screens, end cards, maps with text, or burned-in subtitles. Logos and watermarks are fine. " + LICENSE_OVERLAY_RULE + "Each moment "
    "is one continuous shot or sequence, 3 to 20 seconds. Up to 3 moments per sentence; omit a sentence when nothing in "
    "the video fits. Do not guess from the title; use only what you see. Times are seconds from the start of the video "
    "(numbers). Return JSON only: "
    '{"video_summary":string,"duration_seen":number,"matches":[{"sentence_id":int,"start":number,"end":number,'
    '"confidence":number 0-1,"shows":string,"keywords":[string]}]}\n\nSentences:\n')


def pinpoint_youtube(meta, sentences, out):
    """The moments of a YouTube video that show the given sentences.

    sentences is [(scene_id, narration)]. Returns the verdict
    {url, summary, matches:[{sentence_id, start, end, confidence, shows,
    keywords}]} holding only the matches that pass the filters, or None
    when the video could not be read. The verdict is kept beside the
    windows as <id>.pinpoint.json, so a rerun places the same windows and
    finds its window files in the cache.
    """
    url = "https://www.youtube.com/watch?v=%s" % meta["id"]
    asked = digest([[sid, str(text)] for sid, text in sentences])
    target = Path(out) / "sources" / ("%s.pinpoint.json" % meta["id"])
    if target.is_file():
        cached = load(target)
        if cached.get("url") == url and cached.get("sentences") == asked:
            return cached
    folder = Path(out) / "pinpoint" / str(meta["id"])
    folder.mkdir(parents=True, exist_ok=True)
    prompt = _PINPOINT_PROMPT + "\n".join("%s. %s" % (sid, text) for sid, text in sentences)
    started = time.monotonic()
    try:
        # One request: a second copy of an 80 s call holds another Flash
        # channel for nothing, and the storyboard is the fallback anyway.
        result = api("flash", prompt, folder / "flash.json", urls=[url], tokens=8000,
                     timeout=PINPOINT_TIMEOUT_SECONDS, hedge_override=0, max_attempts_override=1,
                     deadline=time.monotonic() + PINPOINT_TIMEOUT_SECONDS)["data"]
    except Exception as exc:
        event(out, "pinpoint_unavailable", id=meta["id"], error=type(exc).__name__, detail=str(exc)[-200:])
        return None
    duration = float(meta.get("duration") or 0)
    ids = {sid for sid, _ in sentences}
    matches = []
    for m in result.get("matches") or []:
        try:
            sid, a, b, conf = m.get("sentence_id"), float(m.get("start")), float(m.get("end")), float(m.get("confidence"))
        except (TypeError, ValueError):
            continue
        if (sid in ids and math.isfinite(a) and math.isfinite(b) and 0 <= a < b
                and conf >= PINPOINT_MIN_CONFIDENCE and b <= duration - PINPOINT_END_SECONDS):
            matches.append({"sentence_id": sid, "start": round(a, 1), "end": round(b, 1), "confidence": conf,
                            "shows": str(m.get("shows") or ""),
                            "keywords": [str(k) for k in m.get("keywords") or [] if str(k).strip()][:8]})
    verdict = {"url": url, "sentences": asked, "summary": result.get("video_summary"),
               "answered": len(result.get("matches") or []), "matches": matches,
               "seconds": round(time.monotonic() - started, 1), "receipt": str(folder / "flash.json")}
    save(target, verdict)
    event(out, "pinpoint_judged", id=meta["id"], answered=verdict["answered"], kept=len(matches),
          seconds=verdict["seconds"])
    return verdict


def pinpoint_windows(matches, duration, count):
    """The windows to fetch around the pinpointed moments, and what each shows.

    A moment is padded like any cut. Moments closer than the same-origin
    gap cannot give two cuts, so they share one window while it stays
    within RANGE_MAX_SECONDS; every window left can then give a cut of
    its own. The best windows (highest confidence, then most sentences)
    are kept, up to the count the source may give. Returns ([(a, b)],
    [info]) in time order; info holds the scene ids and the matches.
    """
    groups = []
    for m in sorted(matches, key=lambda m: m["start"]):
        a = max(0.0, m["start"] - RANGE_PADDING_SECONDS)
        b = min(duration, m["end"] + RANGE_PADDING_SECONDS)
        if groups and a - groups[-1][1] < MIN_SAME_ORIGIN_GAP_SECONDS and max(b, groups[-1][1]) - groups[-1][0] <= RANGE_MAX_SECONDS:
            groups[-1][1] = max(groups[-1][1], b)
            groups[-1][2].append(m)
        else:
            groups.append([a, b, [m]])
    groups.sort(key=lambda g: (max(m["confidence"] for m in g[2]), len({m["sentence_id"] for m in g[2]})),
                reverse=True)
    windows, info = [], []
    for a, b, inside in sorted(groups[:min(count, RANGE_MAX_WINDOWS)], key=lambda g: g[0]):
        if b - a < RANGE_MIN_SECONDS:
            a = max(0.0, min(a, duration - RANGE_MIN_SECONDS))
            b = min(duration, a + RANGE_MIN_SECONDS)
        windows.append((round(a, 3), round(min(b, a + RANGE_MAX_SECONDS), 3)))
        info.append({"scene_ids": sorted({m["sentence_id"] for m in inside}), "matches": inside})
    return windows, info


_PINPOINT_CHECK_PROMPT = (
    "Each tile is one frame of a video excerpt, labelled with its id. For every id say whether the frame shows any of: "
    "burned-in subtitles that transcribe speech, an end card or end screen, credits, a title card or text-only screen, "
    "a person talking to the camera, or text offering the footage for sale or licensing (e.g. 'Visit StormChasingVideo.com To License'). Other logos, watermarks and channel bugs do not count. "
    "JSON {rows:[{id:string,clean:boolean,problems:[string]}]}, every id exactly once. IDS: ")


def pinpoint_check(rows, out, source_id):
    """One frame of each pinpointed window, checked for what the model missed.

    The pinpoint watched the video, so a window needs no full describe;
    it does not read burned-in subtitles or end cards reliably, and those
    were its wrong answers. One frame of the best moment per window goes
    to Flash in one call. A clean window enters the catalog as VIDEO with
    the pinpoint's description; a flagged one is dropped. When the check
    itself fails the rows come back as they were, without a category, and
    describe_group classifies them the usual way.
    """
    folder = Path(out) / "pinpoint" / str(source_id)
    tiles = []
    for row in rows:
        best = max(row["pinpoint"], key=lambda m: m["confidence"])
        at = (best["start"] + best["end"]) / 2 - row["start"]
        frame = folder / ("%s.jpg" % row["id"])
        try:
            sample(row["path"], max(0.0, min(at, row["local_end"] - 0.5)), frame)
            tiles.append((str(frame), row["id"]))
        except Exception:
            pass
    if not tiles:
        return rows
    try:
        board = contact(tiles, folder / "check.jpg")
        found = api("flash", _PINPOINT_CHECK_PROMPT + str([t[1] for t in tiles]), folder / "check.json", [board],
                    tokens=1200, timeout=INVENTORY_TIMEOUT_SECONDS, hedge_override=INVENTORY_HEDGE_SECONDS,
                    max_attempts_override=1, deadline=time.monotonic() + INVENTORY_TIMEOUT_SECONDS)
        byid = {str(r.get("id")): r for r in found["data"].get("rows") or []}
    except Exception as exc:
        event(out, "pinpoint_check_unavailable", id=source_id, error=type(exc).__name__)
        return rows
    checked = []
    for row in rows:
        verdict = byid.get(row["id"])
        if verdict is None:
            checked.append(row)
            continue
        if verdict.get("clean") is not True:
            event(out, "pinpoint_window_rejected", id=row["id"], problems=verdict.get("problems"))
            continue
        shows = list(dict.fromkeys(m["shows"] for m in row["pinpoint"] if m["shows"]))
        checked.append({**row, "category": "VIDEO", "usable": True, "description": "; ".join(shows)[:400],
                        "keywords": list(dict.fromkeys(k for m in row["pinpoint"] for k in m["keywords"]))[:12],
                        "problems": [], "confidence": max(m["confidence"] for m in row["pinpoint"]),
                        "sample_contact": board, "classification_receipt": str(folder / "flash.json"),
                        "classification_sampling": "pinpoint: Flash watched the YouTube video for the sentences; "
                                                   "one frame per window checked"})
    return checked


def fetch_source_windows(url, meta, out, count=2, prefer_height=1080, sentences=()):
    """Fetch only the parts of a source that the film will use.

    Returns the list of local window files and their source-to-local
    map, or (None, None) when the fetch did not work, in which case
    the caller falls back to the whole file. A source whose storyboard
    shows no clean B-roll returns ([], {"rejected": "storyboard", ...}):
    nothing was fetched and nothing should be.

    With sentences ([(scene_id, narration)]) a YouTube source is
    pinpointed first; each window of the map then carries "pinpoint",
    the scene ids and matches it was fetched for.
    """
    label = "%s_windows" % meta.get("id")
    windows = info = None
    if (PINPOINT and sentences and not meta.get("site")
            and 0 < float(meta.get("duration") or 0) <= PINPOINT_MAX_VIDEO_SECONDS):
        verdict = pinpoint_youtube(meta, sentences, out)
        if verdict is not None and verdict["matches"]:
            windows, info = pinpoint_windows(verdict["matches"], float(meta.get("duration") or 0), count)
    if windows is None and STORYBOARD:
        verdict = judge_storyboard(meta, out)
        if verdict is not None:
            if verdict.get("usable") is False:
                return [], {"rejected": "storyboard", "verdict": verdict}
            # Judged usable but with no range it could name: the
            # judgement places nothing, so the old plan does.
            windows = storyboard_windows(verdict["ranges"], float(meta.get("duration") or 0), count) or None
    if windows is None:
        windows = plan_windows(meta, count)
    if not windows:
        return None, None
    with _DOWNLOAD_SLOTS:
        files, payload = _download_windows(url, out, windows, label,
                                           prefer_height=prefer_height, media_url=meta.get("media_url"))
    if files is None:
        return None, None
    if info:
        # The map is where a resumed run finds which sentence a window
        # was fetched for.
        for window, found in zip(payload["windows"], info):
            window["pinpoint"] = found
        save(Path(out) / "sources" / (label + ".ranges.json"), payload)
    for f in files:
        register_range_map(f, payload)
    return files, payload

def _superseded_video_stems(folder, out=None):
    """The raw source videos that this run replaces with range windows.

    A previous run of the same film leaves its whole-file YouTube
    downloads in the input folder's sources directory. This run fetches
    the same ids again as precise range windows, so those whole-file
    copies are stale duplicates of footage the pool already holds in a
    better scoped form.

    They are expensive rather than harmless. The motion measurement
    reads the whole range of a candidate, and the range of a stale copy
    is the whole film: the measured run spent minutes decoding a
    4013 second download for a shot that uses seconds of it, while the
    fresh window of the same video was measured in about a second.
    """
    stems = set()
    for sdir in (Path(folder) / "sources", (Path(out) / "sources") if out else None):
        if sdir and sdir.is_dir():
            for f in sdir.glob("*.mp4"):
                stems.add(f.stem)
    return stems


def scan_folder(folder, out=None):
    folder_path = Path(folder)
    superseded = _superseded_video_stems(folder_path, out)
    # REWRITE: scan_folder içinde probe() sonuçlarını SHA256 bazlı disk cache'le (scan_folder_probe_cache.json)
    cache_file = folder_path / "scan_folder_probe_cache.json"
    probe_cache = {}
    if cache_file.is_file():
        try:
            probe_cache = load(cache_file)
        except Exception:
            probe_cache = {}
    cache_dirty = False

    rows = []
    for path in sorted(folder_path.rglob("*")):
        if not path.is_file() or any(p in EXCLUDED or p.startswith(".") or p == "scan_folder_probe_cache.json" for p in path.relative_to(folder_path).parts):
            continue
        if path.suffix.lower() not in (".mp4", ".mkv", ".webm", ".mov", ".png", ".jpg", ".jpeg", ".webp"):
            continue
        if path.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov") and path.stem in superseded:
            continue
        file_sha = sha(path)
        row = {"id": "local_" + digest(str(path))[:10], "path": str(path), "sha256": file_sha,
               "source_url": None, "rights": "User-provided asset; rights not inferred"}
        if path.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov"):
            # REWRITE: Probe sonucunu cache'den al veya ffprobe çalıştırıp cache'le
            if file_sha in probe_cache:
                p = probe_cache[file_sha]
            else:
                p = probe(path)
                probe_cache[file_sha] = p
                cache_dirty = True
            dur = float(p["format"]["duration"])
            is_animation = path.parent.name.lower() == "animations" or any(token in path.stem.upper() for token in ("ANIM", "VOX", "HOLO"))
            if is_animation:
                anim_descriptions = {
                    "ANIM01": "High-definition 3D forensic CAD animation comparing original continuous single hanger rod design versus as-built double rod offset split.",
                    "ANIM02": "3D engineering structural simulation showing welded box-beam flange separation and longitudinal weld seam tear.",
                    "ANIM03": "Dynamic 3D kinematics visualization of fourth-floor and second-floor walkway deck drop into Hyatt atrium.",
                    "ANIM04": "Finite element analysis (FEA) HUD visualization showing critical shear stress concentrations along box beam channel.",
                    "ANIM05": "Macro 3D CAD detail showing 1.25-inch retaining nut and washer punching through bottom flange of MC10x8.4 channel.",
                    "ANIM06": "Volumetric structural diagram showing dynamic harmonic dance floor loading and crowd resonance across walkway."
                }
                desc = next((v for k, v in anim_descriptions.items() if k in path.stem.upper()), f"3D forensic structural animation: {path.stem}")
                row.update(
                    kind="3D",
                    category="3D",
                    usable=True,
                    reuse_video=True,
                    description=desc,
                    source_title=path.stem,
                    start=0.,
                    end=dur,
                    confidence=1.0,
                    keywords=["3D animation", "structural forensic", "Hyatt Regency", "engineering"]
                )
            else:
                row.update(kind="UNKNOWN_VIDEO", start=0., end=dur)
        else:
            with Image.open(path) as im:
                im.verify()
            row["kind"] = "PHOTO"
        rows.append(row)

    if cache_dirty:
        try:
            save(cache_file, probe_cache)
        except Exception:
            pass
    return rows

# The contact sheet shows a window at these shares of its length.
_CONTACT_SHARES = (.08, .5, .92)

# The contact frames are sampled in the background as each source
# lands, the same way footage.prefetch takes the fingerprints, so the
# inventory round finds them on disk. Measured on the Kailasa film: the
# first round sampled 306 frames in 53 s after the last download and
# the second 387 frames in 81 s. A frame of a 4K VP9 window costs 1 to
# 4 s of decode and about 735 MB, so the memory gate let two or three
# run at a time and every group waited for its last frame: the first
# group answered 58 s after the round started, 45 s of it sampling.
# The downloads leave the machine idle for minutes, which is where
# these frames now go. On 48 of its windows landing 4.5 s apart, with
# 0.8 GB free, the first answer came 12.5 s into the round instead of
# 73.5 s, and the round took 25 s instead of 110 s; the contact sheets
# were byte identical.
_SAMPLE_WORKERS = 4
_sample_pool = None
_sample_jobs = {}
_sample_lock = threading.Lock()


def _contact_frame(row, seconds, out):
    """The file a row's contact frame at a local second is kept in.

    The key is the file and its content hash, so a window fetched again
    under the same name is sampled again. None without a hash.
    """
    if not row.get("sha256"):
        return None
    key = digest([str(row["path"]), row["sha256"], round(float(seconds), 3)])
    return Path(out) / "inventory" / "frames" / (key[:24] + ".jpg")


def _sample_to(path, seconds, target):
    # Written under another name first, so a half written frame is
    # never taken for a finished one.
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.stem + "_part.jpg")
    sample(path, seconds, part)
    os.replace(part, target)


class _FrameGroup:
    """The contact frames of one file, read in one ffmpeg process.

    run() does the work once: the pool thread that gets there first, or the
    describe_group worker that needs a frame before the pool has reached it
    (a queued group is done inline, as a queued frame was); the other waits.
    """

    def __init__(self, path, items):
        self.path, self.items = path, items
        self._lock = threading.Lock()
        self._done = False

    def run(self):
        with self._lock:
            if self._done:
                return
            self._done = True
            pending = [(s, t) for s, t in self.items if not t.is_file()]
            parts = []
            try:
                for _, t in pending:
                    t.parent.mkdir(parents=True, exist_ok=True)
                    parts.append(t.with_name(t.stem + "_part.jpg"))
                resources.grab_frames(self.path, [(s, p) for (s, _), p in zip(pending, parts)], 640, 60)
                for p, (_, t) in zip(parts, pending):
                    with Image.open(p) as im:
                        im.verify()
                    os.replace(p, t)
            except Exception:
                # One bad second must not lose the others: each frame on its own, as before.
                for (s, t) in pending:
                    if not t.is_file():
                        try:
                            _sample_to(self.path, s, t)
                        except Exception:
                            pass


def prefetch_samples(rows, out):
    """Start sampling the contact frames of landed video rows; returns at once."""
    global _sample_pool
    jobs = []
    for row in rows or []:
        if row.get("kind") != "VIDEO":
            continue
        a, b = _local_bounds(row)
        for f in _CONTACT_SHARES:
            target = _contact_frame(row, a + (b - a) * f, out)
            if target is not None and not target.is_file():
                jobs.append((row["path"], a + (b - a) * f, target))
    if not jobs:
        return
    with _sample_lock:
        if _sample_pool is None:
            _sample_pool = ThreadPoolExecutor(max_workers=_SAMPLE_WORKERS,
                                              thread_name_prefix="contact-prefetch")
        groups = {}
        for path, seconds, target in jobs:
            if target not in _sample_jobs:
                groups.setdefault(str(path), []).append((path, seconds, target))
        for path, all_rows in groups.items():
            for i in range(0, len(all_rows), 6):  # at most 6 inputs in one process
                rows = all_rows[i:i + 6]
                group = _FrameGroup(rows[0][0], [(seconds, target) for _, seconds, target in rows])
                for _, _, target in rows:
                    _sample_jobs[target] = group
                _sample_pool.submit(group.run)


def _contact_sample(path, seconds, output, cached):
    """sample(), copied from the frame taken when the source landed if there is one."""
    if cached is not None:
        with _sample_lock:
            job = _sample_jobs.pop(cached, None)
        # A group still queued behind the others is read here instead
        # of waiting for its turn; one that is being read is awaited.
        if job is not None:
            try:
                job.run()
            except Exception:
                pass
        if cached.is_file():
            shutil.copyfile(cached, output)
            return str(output)
    return sample(path, seconds, output)


def describe_group(rows, index, out):
    set_context(out)
    try:
        return _describe_group(rows, index, out)
    except RuntimeError as exc:
        event(out, "inventory_group_unavailable", group=index, count=len(rows), error=str(exc)[-600:])
        return _heuristic_group(rows, index, out, "flash timeout")

def _heuristic_group(rows, index, out, reason):
    """Keep real probed media flowing after a Flash timeout; later gates inspect it."""
    result = []
    for row in rows:
        if row.get("category") == "3D" and row.get("usable"):
            result.append(row)
            continue
        # REWRITE: _heuristic_group'a pre_filter_quality çağrısı eklendi — reject edilmesi gerekenler usable=True geçmesin
        quality_ok, quality_reason = pre_filter_quality(row, out)
        if not quality_ok:
            result.append({**row, "category": "REJECT", "description": f"Pre-filter: {quality_reason}",
                           "keywords": [], "usable": False, "problems": [quality_reason],
                           "classification_receipt": None, "classification_sampling": "deterministic_pre_filter",
                           "fallback": True, "fallback_reason": reason})
            continue
        suffix = Path(str(row.get("path", ""))).suffix.lower()
        category = "VIDEO" if suffix in {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"} else (row.get("kind") or "PHOTO")
        desc = row.get("description") or row.get("source_title") or Path(row.get("path", "")).stem.replace("_", " ")
        result.append({**row, "category": category, "description": desc, "usable": True,
                       "confidence": 0.55, "fallback": True,
                       "fallback_reason": reason,
                       "classification_sampling": "local probe fallback"})
    event(out, "inventory_group_fallback", group=index, count=len(result), reason=reason)
    return result

def _describe_group(rows, index, out):
    folder = Path(out) / "inventory" / f"group_{index:03}"
    folder.mkdir(parents=True, exist_ok=True)
    # Check if all rows are pre-verified 3D animations
    if all(r.get("category") == "3D" and r.get("usable") for r in rows):
        return [{**r, "classification_receipt": "local_animation_preverified", "classification_sampling": "pre-rendered 1080p CAD animation"} for r in rows]

    # Reuse a complete prior classification for the same ordered IDs
    cached = load(folder / "flash.json") if (folder / "flash.json").is_file() else {}
    cached_rows = cached.get("data", {}).get("rows") if isinstance(cached, dict) else None
    expected_ids = {r["id"] for r in rows if not (r.get("category") == "3D" and r.get("usable"))}
    if isinstance(cached_rows, list) and {r.get("id") for r in cached_rows} == expected_ids:
        board = str(folder / "contact.jpg") if (folder / "contact.jpg").is_file() else None
        byid = {r["id"]: r for r in cached_rows}
        output = []
        for row in rows:
            if row.get("category") == "3D" and row.get("usable"):
                output.append({**row, "classification_receipt": "local_animation_preverified", "classification_sampling": "pre-rendered 1080p CAD animation"})
                continue
            value = byid.get(row["id"], {})
            if value.get("category") not in ("VIDEO", "PHOTO", "2D", "3D", "REJECT"):
                break
            output.append({**row, **value, "sample_contact": board,
                           "classification_receipt": str(folder / "flash.json"),
                           "classification_sampling": "cached actual source frames"})
        if len(output) == len(rows):
            event(out, "inventory_group", group=index, count=len(rows),
                  usable=sum(x.get("usable") is True for x in output), cached=True)
            return output

    unverified = []
    tile_specs = []
    sample_jobs = []

    for row in rows:
        if row.get("category") == "3D" and row.get("usable"):
            continue
        unverified.append(row)
        if row.get("kind") in ("PHOTO", "2D") and Path(row["path"]).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            tile_specs.append((str(row["path"]), str(row["id"])))
        else:
            a, b = _local_bounds(row)
            for j, f in enumerate(_CONTACT_SHARES):
                frame_path = str(folder / f'{row["id"]}_{j}.jpg')
                # A fetched window carries a source second, so the
                # label names the source second and the file names the
                # local one. The two are not the same number.
                if row.get("range_file"):
                    at = float(row.get("source_start", 0)) + (a + (b - a) * f)
                    label = f'{row["id"]} / kaynak {at:.1f}s'
                else:
                    label = f'{row["id"]} / {(a+(b-a)*f):.1f}s'
                tile_specs.append((frame_path, label))
                sample_jobs.append((row["path"], a + (b - a) * f, frame_path,
                                    _contact_frame(row, a + (b - a) * f, out)))

    if not unverified:
        return [{**r, "classification_receipt": "local_animation_preverified", "classification_sampling": "pre-rendered 1080p CAD animation"} for r in rows]

    # REWRITE: sample() çağrıları ThreadPoolExecutor max_workers=4 ile paralel yapıldı
    if sample_jobs:
        def _try_sample(job):
            try:
                return _contact_sample(*job)
            except Exception:
                return None
        with ThreadPoolExecutor(max_workers=4) as sample_pool:
            list(sample_pool.map(_try_sample, sample_jobs))
        # A frame ffmpeg could not write (a second past a short window's
        # end) is left off the board; it crashed stage 3 after 61 minutes.
        tile_specs = [t for t in tile_specs if Path(t[0]).is_file()]
        if not tile_specs:
            return [{**r, "category": "REJECT", "usable": False, "problems": ["no frame could be sampled"]}
                    for r in unverified]

    board = contact(tile_specs, folder / "contact.jpg")
    evidence = [{k: r.get(k) for k in ("id", "kind", "start", "end", "description", "source_title")} for r in unverified]
    try:
        result = api("flash", 'Classify each REAL sampled asset. JSON {rows:[{id,category:VIDEO|PHOTO|2D|3D|REJECT,usable:boolean,description:string,keywords:[string],problems:[string],tone:string,composition:string}]}. '
                 'VIDEO requires moving live camera footage; a slideshow/photo or animation is not VIDEO. USER DIRECTIVE: All documentary videos, news reports, b-roll, and historical footage from YouTube, the Internet Archive, Wikimedia Commons or NASA are pre-cleared by user policy and FULLY ELIGIBLE as VIDEO. Do NOT reject videos for presenter/interview shots or modern documentary presentation; mark them as usable VIDEO. '
                 # Burned-in subtitles are the one on-screen text that
                 # disqualifies footage: the viewer takes them for the
                 # film's own captions and expects them to follow the
                 # narration. Every other overlay is left alone, and is
                 # kept out of problems because the selector reads them.
                 'Logos, watermarks, channel bugs, LIVE or timestamp tags, news graphics, banners, lower thirds, slides and title cards are NOT problems: never reject for them and never list them in problems. ' + LICENSE_OVERLAY_RULE +
                 'The one on-screen-text defect is burned-in subtitles, caption text that transcribes the speech: mark such an asset usable false and list "burned-in subtitles" in problems. '
                 + profiles.for_run(out).get("prompt_note", "") +
                 '2D/3D diagrams with wrong load labels or fake FEA measurements are unusable unless a correct safe subrange is separately inspected. '
                 'Do not reject real archival footage merely because its reuse license is not known; licensing stays a separate explicit report. Explain visible content precisely, not conjecture. '
                  'Every ID exactly once. Samples only, not full-frame/full-motion authentication. ASSETS:' + str(evidence), folder / "flash.json", [board], tokens=2200, timeout=INVENTORY_TIMEOUT_SECONDS, reuse_failed=False, hedge_override=INVENTORY_HEDGE_SECONDS, max_attempts_override=1, deadline=time.monotonic()+INVENTORY_TIMEOUT_SECONDS)
    except RuntimeError as exc:
        event(out,"inventory_group_unavailable",group=index,count=len(rows),error=str(exc))
        return _heuristic_group(rows, index, out, "flash timeout")
    # An answer that left out an id, or gave one a category that does not
    # exist, stopped the whole film (TOPIC_2, 2.7 minutes into stage 3).
    # Ids the model invented are ignored; a row it did not classify takes
    # the probe fallback, as a timed-out group does.
    byid = {r.get("id"): r for r in (result["data"].get("rows") or []) if isinstance(r, dict)}
    output = []
    for row in rows:
        if row.get("category") == "3D" and row.get("usable"):
            output.append({**row, "classification_receipt": "local_animation_preverified", "classification_sampling": "pre-rendered 1080p CAD animation"})
            continue
        value = byid.get(row["id"])
        if value is None or value.get("category") not in ("VIDEO", "PHOTO", "2D", "3D", "REJECT"):
            output.extend(_heuristic_group([row], index, out, "missing from the classification"))
            continue
        output.append({**row, **value, "sample_contact": board, "classification_receipt": str(folder / "flash.json"),
                       "classification_sampling": "three actual source frames per source-shot; not continuous viewing"})
    event(out, "inventory_group", group=index, count=len(rows), usable=sum(x.get("usable") is True for x in output))
    return output

def _box_to_percent(box, page_size):
    """Bring the model's figure box into page percentages.

    The live run failed every PDF group with "Invalid PDF figure crop".
    The cause was the unit: the model answers in normalized 0..1000
    coordinates (the convention for a vision model) while the check
    wanted percentages, so 0<=x<=100 rejected every box. The report's
    own photographs, the collapse pictures in the cited pages, never
    entered the material.

    Three conventions are accepted and converted to percentages, which
    is what the crop needs: percentages (0..100), normalized
    (0..1000), and raw pixels of the page.
    """
    values = [float(v) for v in box]
    width, height = page_size
    highest = max(values)
    if highest <= 100:
        return values
    if highest <= 1000:
        return [v * 100.0 / 1000.0 for v in values]
    return [v * 100.0 / (width if i % 2 == 0 else height)
            for i, v in enumerate(values)]


def document_regions(document, out):
    """Find actual figure regions on cited pages, retaining the unmodified page and OCR."""
    path = Path(document["path"])
    if not path.is_file() or sha(path) != document["sha256"]:
        raise ValueError("Registered document changed")
    prefix = "pdf_" + document["sha256"][:10]
    directory = Path(out) / "sources" / prefix
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "crops.json"
    # The crop rule is part of the identity. The live run found the
    # report's photographs answered in normalized coordinates while the
    # check wanted percentages, so every group failed and the cache
    # kept an empty list under the document's own identity. Without the
    # rule in the identity the cache stays valid and the fix never
    # runs.
    #
    # v4 reads the category under the name the reviewer used, so a
    # region spelled "label" is kept instead of raising. The rule
    # changed, so the version changed too, or the cache would keep the
    # broken answer.
    identity = digest({"document": document, "crop_rule": "box-to-percent-v4"})
    if target.exists() and load(target).get("identity") == identity:
        return load(target)["assets"]
    pdf = pymupdf.open(path)
    pages = document.get("candidate_pages", [])
    if not pages:
        pages = [i+1 for i, p in enumerate(pdf) if re.search(r"figure|photograph|diagram", p.get_text(), re.I)][:24]
    for n in pages:
        pdf[n-1].get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(directory / f"page_{n}.png")
    page_text = {n: pdf[n-1].get_text()[-1400:] for n in pages}
    pdf.close()

    def crop_group(item):
        set_context(out)
        index, group = item
        board = contact([(directory/f"page_{n}.png", f"PDF page {n}") for n in group], directory / f"board_{index}.jpg", columns=2, cell=(660, 930))
        texts = {n: page_text[n] for n in group}
        review = api("flash", 'Locate actual photographic or engineering diagram FIGURES on these cited report pages. '
                     'Exclude surrounding paragraphs, page numbers, captions and white margins. Return JSON '
                     '{regions:[{page:integer,box:[left,top,right,bottom],category:PHOTO|2D,caption:string}]}. '
                     'Coordinates are normalized 0..1000 of each ORIGINAL full page (NOT contact sheet), preserve the whole subject. '
                     'At most two regions per page. PHOTO must be a real camera/microscope image; graphs and diagrams are2D. '
                     'Caption must use page OCR, never invent figure identity. OCR:' + str(texts), directory / f"crop_flash_{index}.json", [board], tokens=2200,timeout=60)["data"] or {}
        assets = []
        # The reviewer answers the shape the prompt asks for, but it
        # sometimes writes the category under "label" instead. Reading
        # it with a hard index turned that variation into a KeyError,
        # and the KeyError took the whole group of four cited pages
        # with it: the run lost the collapse photographs on pages 59
        # to 62 because one region of the first group was spelled
        # differently from the others. A field the reviewer may name
        # either way is read the way it was answered, and a region
        # that names it neither way is skipped like any other.
        for j, region in enumerate(review.get("regions") or []):
            n, box = region.get("page"), region.get("box")
            category = region.get("category") or region.get("label")
            if n not in group or not isinstance(box, (list, tuple)) or len(box) != 4 or not all(isinstance(x, (float, int)) and math.isfinite(x) for x in box) or category not in ("PHOTO", "2D"):
                event(out, "pdf_figure_region_skipped", reason="malformed_region", page=n)
                continue
            source = directory / f"page_{n}.png"
            output = directory / f"figure_{n}_{j}.jpg"
            # One bad region must not cost the whole group. The live run
            # lost four pages of the report because a single box came
            # back with its right edge before its left edge, and the
            # raise took the other four valid regions of that group
            # with it.
            with Image.open(source) as im:
                percent = _box_to_percent(box, im.size)
                if box[2] <= box[0] or box[3] <= box[1]:
                    event(out, "pdf_figure_region_skipped", reason="inverted_box", page=n)
                    continue
                if not all(0 <= v <= 100 for v in percent):
                    event(out, "pdf_figure_region_skipped", reason="out_of_range", page=n)
                    continue
                region_im = im.crop(tuple(round(v * (im.width if i % 2 == 0 else im.height) / 100) for i, v in enumerate(percent)))
                if min(region_im.size) < 120:
                    event(out, "pdf_figure_region_skipped", reason="too_small", page=n)
                    continue
                region_im.convert("RGB").save(output, quality=95)
            assets.append({"id": f"{prefix}_{n}_{j}", "kind": category, "path": str(output), "sha256": sha(output),
                           "description": str(region.get("caption", "")), "source_url": document["url"], "page": n,
                           "crop_percent": [round(v, 3) for v in percent],
                           "crop_box_as_answered": [round(float(v), 3) for v in box],
                           "source_document": str(path), "source_document_sha256": document["sha256"],
                           "rights": "Report can contain third-party photographs; private review only until rights checked"})
        return assets
    crops = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(crop_group, item) for item in enumerate([pages[i:i+4] for i in range(0,len(pages),4)])]
        for future in as_completed(futures):
            try:
                crops.append(future.result())
            except Exception as exc:
                event(out, "optional_document_group_failed", error=type(exc).__name__)
    result = [r for group in crops for r in group]
    save(target, {"identity": identity, "assets": result})
    return result

def shortlist(rows, budget, admitted_origins=None):
    """Spread video windows across sources and source time; prioritize unrepresented origins."""
    admitted = admitted_origins or set()
    videos = {}; other = []
    for row in rows:
        if row.get("kind") == "VIDEO":
            videos.setdefault(origin_id(row), []).append(row)
        else:
            other.append(row)
    # Sort origins: those NOT yet admitted come first to ensure maximum source diversity
    sorted_origins = sorted(videos.keys(), key=lambda o: (o in admitted, o))
    ordered = []
    for origin in sorted_origins:
        group = sorted(videos[origin], key=lambda r: r["start"])
        indices = []; pending = [(0, len(group) - 1)]
        while pending:
            low, high = pending.pop(0)
            if low > high: continue
            mid = (low + high) // 2; indices.append(mid)
            pending.extend(((low, mid - 1), (mid + 1, high)))
        ordered.append([group[i] for i in indices])
    picked = []
    while any(ordered) and len(picked) < budget:
        for group in ordered:
            if group and len(picked) < budget:
                picked.append(group.pop(0))
    return other + picked

def pool_capacity(assets):
    def capacity(native=False):
        groups = {}
        for row in assets:
            if row.get("usable") and row.get("category") == "VIDEO" and (not native or int(row.get("height") or row.get("native_height") or 0) >= 1080):
                # A whole local file kept by the Flash-timeout fallback has
                # no window, only its duration; indexed as r["end"] it
                # crashed stage 3 after 31 minutes (PAR_1..4, 2026-10-27).
                start = float(row.get("start") or 0.0)
                end = row.get("end")
                end = float(end) if end is not None else start + float(row.get("duration") or 0.0)
                groups.setdefault(origin_id(row), []).append({"start": start, "end": end})
        total = 0
        for group in groups.values():
            # REWRITE: O(n²) iç döngü -> bisect ve suffix_max ile O(n log n) optimize edildi
            durations = [r["end"] - r["start"] for r in group]
            best = max(durations, default=0)
            if len(group) >= 2:
                sorted_group = sorted(group, key=lambda r: r["start"])
                starts = [r["start"] for r in sorted_group]
                durs = [r["end"] - r["start"] for r in sorted_group]
                n = len(sorted_group)
                suffix_max = [0.0] * (n + 1)
                for i in range(n - 1, -1, -1):
                    suffix_max[i] = max(suffix_max[i + 1], durs[i])
                for a in sorted_group:
                    a_dur = a["end"] - a["start"]
                    target_start = a["end"] + 60.0
                    idx = bisect.bisect_left(starts, target_start)
                    if idx < n:
                        best = max(best, a_dur + suffix_max[idx])
            total += best
        return total
    groups = {}
    for row in assets:
        if row.get("usable") and row.get("category") == "VIDEO":
            groups.setdefault(origin_id(row), []).append(row)
    return {
        "video_seconds": round(capacity(), 3),
        "native_hook_seconds": round(capacity(True), 3),
        "unique_videos": len(groups),
        "photos": len({r.get("sha256") or r["id"] for r in assets if r.get("usable") and r.get("category") == "PHOTO"}),
    }

def _library_rows(sentences, out):
    """The windows the local BBC library holds for the film's sentences."""
    from . import bbc_library
    try:
        started = time.monotonic()
        # Each sentence is searched with three concrete descriptions of
        # what a camera would see (one Flash call per 30 sentences).
        expansions = bbc_library.expand(sentences, Path(out) / "library")
        matches = bbc_library.search(sentences, expansions=expansions)
        rows = bbc_library.cut_windows(matches, out) if matches else []
        event(out, "library_windows", matches=len(matches), windows=len(rows),
              sentences=len({m["scene_id"] for m in matches}), expanded=len(expansions),
              seconds=round(time.monotonic() - started, 1))
        return rows
    except Exception as exc:
        event(out, "library_unavailable", error=type(exc).__name__, detail=str(exc)[-200:])
        return []


def prepare(timeline, out, expansion_round=0, missing_cuts=None):
    out = Path(out)
    ensure_pot_server(out)
    folder = Path(timeline["input_folder"])
    # The film's production profile (settings.json): its mix, its priority
    # channels and its search languages. The default profile has none of
    # the extras, so its prompts and searches are the ones it always had.
    production = profiles.for_run(out)
    restrict_channels(production, out)
    if production["targets"].get("PHOTO", 0) or production["targets"].get("CARD", 0):
        ensure_searxng(out)
    languages = production.get("languages") or ()
    channels = production.get("priority_channels") or ()
    video_share = production["targets"]["VIDEO"] / 100
    # A CARD shot is built from a photograph, so the photo pool covers both.
    photo_share = (production["targets"]["PHOTO"] + production["targets"].get("CARD", 0)) / 100
    search_options = {k: production[k] for k in ("sites", "channel_take") if k in production}
    # The sentences a YouTube source is pinpointed for.
    sentences = [(s["scene_id"], s["narration"]) for s in timeline["scenes"] if str(s.get("narration") or "").strip()]
    pinpoint_turns = itertools.count()
    # The priority channels are searched with short topics of their own
    # (below), not with the long footage queries: a channel's own search
    # answered "Siberian tiger walking in deep snow winter taiga footage"
    # with almost nothing, and "Siberian tiger" with ten BBC Earth films.
    expansion_hint = (" This is a bounded expansion round after the previous candidate pool could not satisfy the approved mix. "
                      "Generate materially different queries that target missing visual categories, archival photographs, "
                      "institutional collections and complementary camera footage; do not repeat the prior queries."
                      if expansion_round else "")
    channel_hint = ("Also write 8-12 short channel topics, each 1-3 words naming an animal, place or behaviour the film "
                    "shows (e.g. \"Siberian tiger\", \"tiger boar\", \"brown bear winter\"); they are searched inside "
                    "natural-history channels; JSON field channel_topics:[string]. " if channels else "")
    localized_hint = (("Also write 3 footage search queries in each of these languages (ISO 639-1 codes: %s), in the words "
                       "an uploader of nature footage in that language would use, covering the main animals and beats; "
                       "JSON field localized_queries:{code:[string]}. ") % ", ".join(languages) if languages else "")
    overview = api("flash", 'Extract the documentary subject and 8-10 diverse footage search queries (each one is run on YouTube, the Internet Archive, Wikimedia Commons and NASA) covering ALL narrative beats and acts from beginning to end. '
                   + production.get("catalog_brief", 'The film needs footage to cut, not people talking: target archival film and news footage of the event, rescue and recovery footage, construction and structure footage, engineering animations and reconstructions, raw or b-roll footage, and location walkthroughs. ') +
                   'Avoid queries that mostly return interviews, podcasts, lectures, reaction videos, commentary or studio news anchors. '
                   'No file operations or rewriting. JSON {topic:string,search_queries:[string],keywords:[string]}. '
                   + channel_hint + localized_hint + expansion_hint +
                   'Narration beats: ' + str([{k:s[k] for k in ("scene_id","narrative_beat")} for s in timeline["scenes"]]), out / "topic_flash.json", tokens=1400, hedge_override=30, timeout=90, max_attempts_override=2)["data"]
    prior_queries=[]
    prior_search=(out / f"source_search_replan_{expansion_round-1}.json"
                  if expansion_round and (out / f"source_search_replan_{expansion_round-1}.json").exists()
                  else out / "source_search.json")
    if expansion_round and prior_search.exists():
        prior_queries=load(prior_search).get("queries",[])
    fresh_queries=[overview["topic"]]+overview.get("search_queries",[])
    if expansion_round:
        prior_set={str(q).strip().casefold() for q in prior_queries}
        fresh_queries=[q for q in fresh_queries if str(q).strip().casefold() not in prior_set]
    queries=list(dict.fromkeys(fresh_queries + prior_queries))[:(12 if expansion_round else 8)]
    def lookup(item):
        index,query=item;folder=out/"searches"/f"query_{index}";folder.mkdir(parents=True,exist_ok=True)
        if expansion_round:
            folder=out/"searches"/f"replan_{expansion_round}_query_{index}";folder.mkdir(parents=True,exist_ok=True)
        return search(query,folder,archive=False,**search_options)["candidates"]
    # Queries in the profile's other languages run on YouTube only, after
    # the English ones, so the priority channels keep the head of the list.
    localized=[(lang,str(q).strip()) for lang,items in (overview.get("localized_queries") or {}).items()
               if lang in languages and isinstance(items,list) for q in items[:3] if str(q).strip()]
    def lookup_localized(item):
        index,(lang,query)=item
        folder=out/"searches"/((f"replan_{expansion_round}_" if expansion_round else "")+f"{lang}_query_{index}")
        return search(query,folder,sites=("youtube",),limit=production.get("localized_take",10))["candidates"]
    topics=[str(t).strip() for t in (overview.get("channel_topics") or []) if str(t).strip()][:12] if channels else []
    def lookup_channels(item):
        index,topic=item
        folder=out/"searches"/((f"replan_{expansion_round}_" if expansion_round else "")+f"channel_topic_{index}")
        folder.mkdir(parents=True,exist_ok=True)
        return search(topic,folder,sites=(),channels=channels,channel_take=production.get("channel_take",10))["candidates"]
    with ThreadPoolExecutor(max_workers=production.get("search_workers",6)) as pool:
        found=(list(pool.map(lookup_channels,enumerate(topics)))+list(pool.map(lookup,enumerate(queries)))
               +list(pool.map(lookup_localized,enumerate(localized))))
    search_result={"queries":queries,"candidates":list({c["id"]:c for rows in found for c in rows}.values())}
    # A priority channel's video found by the general search is flagged
    # too, so the selector takes it first like a channel hit.
    priority_ids=set(production.get("priority_channel_ids") or ())
    for c in search_result["candidates"]:
        if c.get("channel_id") in priority_ids:c["priority_channel"]=True
    if localized:search_result["localized_queries"]=localized
    if topics:search_result["channel_topics"]=topics
    search_result["source_priority_policy"] = SOURCE_PRIORITY_RULE
    search_result["source_priority_order"] = ["semantic_fit", "truthful_provenance", "native_4k_1080p", "native_720p", "lower_resolution"]
    save(out/(f"source_search_replan_{expansion_round}.json" if expansion_round else "source_search.json"),search_result)

    # Shots are about four seconds and a recording gives at most three
    # cuts; half of the candidates are lost to talking heads and shaky
    # material, so the pool is sized with that margin.
    needed_video_shots = math.ceil(float(timeline["audio_duration_sec"]) * video_share / 4)
    source_budget = max(16, min(80, len(search_result["candidates"]), math.ceil(needed_video_shots / MAX_USES_PER_ORIGIN * 2) + 8))
    # An expansion round only covers the measured gap: Gobekli Tepe was 20
    # clean cuts short and the round fetched another full pool (~180
    # sources, ~15 minutes) for it.
    if expansion_round and missing_cuts is not None:
        source_budget = max(6, min(source_budget, math.ceil(missing_cuts / MAX_USES_PER_ORIGIN * 2) + 4))

    # REWRITE: candidates kompakt serialize et — sadece {id, title, duration_sec, channel} gönder
    # Full metadata candidate_map'te tutulur, seçilen id'ler map üzerinden çekilir
    candidate_map = {c["id"]: c for c in search_result["candidates"]}
    compact_candidates = [
        {
            "id": c.get("id"),
            "title": c.get("title"),
            "duration_sec": c.get("duration"),
            "channel": c.get("channel"),
            "site": c.get("site", "youtube"),
            **({"priority_channel": bool(c.get("priority_channel"))} if channels else {})
        }
        for c in search_result["candidates"]
    ]

    selection = api("flash", SOURCE_PRIORITY_RULE+f' Select up to {source_budget} of these actual search candidates (YouTube, Internet Archive, Wikimedia Commons, NASA) to cover the FULL story with camera footage. '
                    'Logos, watermarks, LIVE tags, news graphics, lower thirds and title cards in a video are no reason to skip it, but never select footage sold by a stock or licensing seller (e.g. StormChasingVideo / SCV, ViralHog, Jukin, Newsflare, Pond5, Getty). '
                    'One source video may supply at most three separated excerpts, at least 30 seconds apart, so select a broad, diverse pool covering ' + production.get("selection_brief", "disaster, rescue, engineering, investigation, legal aftermath, and modern context") + '. '
                    'Prefer videos whose picture is mostly footage (archival film, rescue, construction, engineering animation, location) over interviews, lectures, podcasts, commentary or studio-anchor segments, because a person talking to the camera cannot be used. '
                    + ('Candidates with priority_channel true come from the BBC natural-history channels: select them first wherever they fit a beat, and take other channels only for the beats they do not cover. ' if channels else '') +
                    'JSON {ids:[string],reason:string}. Topic:' + overview["topic"] + '\n' + str(compact_candidates),
                    out / "source_selection_flash.json", tokens=1200, hedge_override=30, timeout=90, max_attempts_override=2)["data"]
    rows = scan_folder(folder, out=out)
    registry_path = SCRIPTS / "documentary_material_library.json"
    registry = load(registry_path) if registry_path.exists() else []
    matched = [r for r in registry if any(w.lower() in overview["topic"].lower() for w in r.get("topic_keywords", []))]
    documents = []
    for library in matched:
        for r in library.get("assets", []):
            if Path(r["path"]).is_file() and sha(r["path"]) == r["sha256"]:
                rows.append(r.copy())
        documents.extend(library.get("documents", []))
    for document in documents:
        try:
            rows.extend(document_regions(document, out))
        except Exception as exc:
            # A PDF figure locator is additive; known hash-verified crops remain valid
            # when an optional page review times out.
            event(out, "document_region_review_unavailable", error=type(exc).__name__, document=document["url"])
    videos = []
    selected = []
    # REWRITE: candidate_map üzerinden O(1) id eşleştirmesi
    for cid in selection.get("ids", []):
        candidate = candidate_map.get(cid)
        if candidate is None:
            # One id the model made up failed stage 3 of a whole film; the
            # rest of its selection is still good.
            event(out, "source_selector_invented_id", id=str(cid)[:80])
            continue
        selected.append((cid, candidate["url"]))
    def fetch_selected(item):
        cid, url = item
        try:
            meta = download(url, out)
            event(out, "source_ready", id=cid, duration=float(meta["probe"]["format"]["duration"]))
            return meta
        except Exception as exc:
            event(out, "source_unavailable", id=cid, error=type(exc).__name__)
            return None
    # Explicitly configured known sources are still verified by hash and sampled classification.
    library_urls = [url for library in matched for url in library.get("video_urls", [])
                    if url not in {url for _,url in selected}]
    def fetch_library(url):
        try:
            return download(url, out)
        except Exception as exc:
            event(out, "source_unavailable", url=url, error=type(exc).__name__)
            return None
    def fetch_and_probe(item):
        set_context(out)
        meta=fetch_selected(item)
        return scene_shots(meta,out) if meta else []

    def fetch_partial(item):
        """Fetch only the parts of a source the film will use.

        The delivered run pulled 9.05 GB across 168 sources and used
        287.5 s of it, which is 1.2 percent of the downloaded footage.
        A source whose scene scan does not need its body can be
        fetched as a range instead of as a whole file, which is what
        this does.

        A source of 90 seconds or less is scene-scanned, so it needs
        its body and is fetched whole. A longer source is split into
        deterministic 14 second windows without reading the file, so
        only the windows the film may use are fetched.
        """
        cid, url = item
        set_context(out)
        try:
            meta = probe_source(url, out)
        except Exception as exc:
            event(out, "source_metadata_unavailable", id=cid, error=type(exc).__name__)
            return []
        duration = float(meta.get("duration") or 0)
        if duration <= 0:
            return []
        if duration <= 90:
            # Small enough to fetch whole and scene-scan.
            try:
                with _DOWNLOAD_SLOTS:
                    full = download(url, out)
            except Exception as exc:
                event(out, "source_unavailable", id=cid, error=type(exc).__name__)
                return []
            event(out, "source_ready", id=cid, duration=duration)
            return scene_shots(full, out)
        # A long source: fetch the windows, then describe the source
        # from the window files. One window per recording capped the
        # catalog at one cut per source (43 clean cuts for a 15-minute
        # film), so a recording is fetched with as many separated
        # windows as it may give cuts.
        asked = sentences if next(pinpoint_turns) < PINPOINT_MAX_SOURCES else ()
        files, payload = fetch_source_windows(url, meta, out, count=MAX_USES_PER_ORIGIN, sentences=asked)
        if payload and payload.get("rejected"):
            # Its storyboard showed no clean B-roll: the whole file
            # would only be the same talking heads.
            event(out, "source_rejected", id=cid, reason=payload["rejected"],
                  problems=(payload.get("verdict") or {}).get("problems"))
            return []
        if not files:
            # The range fetch did not work, so the whole file is the
            # safe path.
            try:
                with _DOWNLOAD_SLOTS:
                    full = download(url, out)
            except Exception as exc:
                event(out, "source_unavailable", id=cid, error=type(exc).__name__)
                return []
            event(out, "source_ready", id=cid, duration=duration)
            return scene_shots(full, out)
        rows = []
        for index, window in enumerate(payload.get("windows") or []):
            if index >= len(files):
                break
            f = files[index]
            span = window["length_sec"]
            if span < 2:
                continue
            # The row carries the SOURCE second, because the overlap
            # rule, the use cap and the freeze check are all written
            # against the source. The window map says where that
            # second lives inside the file.
            rows.append({"id": "%s_%03d" % (meta.get("id"), index), "kind": "VIDEO",
                         "path": str(f),
                         "start": window["source_start"],
                         "end": window["source_end"],
                         "local_start": 0.0,
                         "local_end": span,
                         "sha256": sha(f),
                         "source_url": meta.get("url"), "source_title": meta.get("title"),
                         "rights": meta.get("rights"),
                         "native_width": int(meta.get("width") or 0),
                         "native_height": int(meta.get("height") or 0),
                         "source_start": window["source_start"],
                         "source_end": window["source_end"],
                         "range_file": True,
                         **({"scene_ids": window["pinpoint"]["scene_ids"],
                             "pinpoint": window["pinpoint"]["matches"]} if window.get("pinpoint") else {})})
        if not rows:
            # Every window came back too short to be useful, so the
            # whole file is the safe path.
            try:
                with _DOWNLOAD_SLOTS:
                    full = download(url, out)
            except Exception as exc:
                event(out, "source_unavailable", id=cid, error=type(exc).__name__)
                return []
            event(out, "source_ready", id=cid, duration=duration)
            return scene_shots(full, out)
        if all(r.get("pinpoint") for r in rows):
            rows = pinpoint_check(rows, out, meta.get("id"))
        event(out, "source_ready", id=cid, duration=duration, partial=True,
             windows=len(rows))
        return rows
    cached_sources = []
    for sdir in [out / "sources", Path(folder) / "sources"]:
        if sdir.is_dir():
            for vid_file in sorted(sdir.glob("*.mp4")):
                vid_id = vid_file.stem
                # A fetched window is a piece of a video, not a video of
                # its own. Its name ends in "_windows_000", so it was
                # entered into the download list as if it were a YouTube
                # id, and 22 of the 63 sidecars were written with the
                # broken url "watch?v=<id>_windows_000". The window is
                # already on disk and its map is in the sidecar, so the
                # piece is not downloaded again.
                # A library window (bbc_<episode>_000) is cut from a local
                # episode, not fetched; its rows come from the library.
                if "_windows" in vid_id or vid_id.startswith("bbc_"):
                    continue
                if vid_id not in {cid for cid, _ in selected} and vid_id not in {cid for cid, _ in cached_sources}:
                    # An archive file's id is not a YouTube id; its page
                    # URL is in the metadata saved beside it.
                    saved = vid_file.with_suffix(".json")
                    url = load(saved).get("url") if saved.is_file() else None
                    cached_sources.append((vid_id, url or f"https://www.youtube.com/watch?v={vid_id}"))
            # A source fetched as windows has only its sidecar, so an
            # expansion round dropped it from the pool. Its url is in the
            # sidecar; the fetch returns the cached windows.
            for sidecar in sorted(sdir.glob("*_windows.ranges.json")):
                vid_id = sidecar.name[:-len("_windows.ranges.json")]
                try:
                    url = load(sidecar).get("url")
                except Exception:
                    continue
                if url and vid_id not in {cid for cid, _ in selected} and vid_id not in {cid for cid, _ in cached_sources}:
                    cached_sources.append((vid_id, url))
    tasks=list(dict(selected+cached_sources+[(f"library_{i}",url) for i,url in enumerate(library_urls)]).items())
    if tasks:
        # DOWNLOAD-COST FIX: 8 parallel downloads left the network idle
        # between requests (the production run finished 76 sources in 411 s
        # with bursts of only 2-4 at a time). 12 keeps the pipe full.
        #
        # PARTIAL DOWNLOAD: a source longer than 90 seconds is fetched as
        # the windows the film may use instead of as a whole file. The
        # measured difference on the same 12 sources: 38.89 s and 658 MB
        # whole against 12.62 s and 1.27 MB as ranges.
        #
        # CONCURRENCY: measured with the production format string, two
        # windows per source, over twelve sources, two rounds each, in a
        # fresh directory per fetch so no run could inherit another's
        # files:
        #
        #   2 parallel   128.46 s and 145.32 s   11/12 and 12/12
        #   4 parallel    78.19 s and  77.64 s   12/12 and 12/12
        #   6 parallel    57.53 s and  57.70 s   12/12 and 12/12
        #   8 parallel    46.44 s and  47.45 s   12/12 and 12/12
        #  12 parallel    36.19 s and  36.56 s   12/12 and 12/12
        #
        # The production format string was measured separately because
        # it is the one that has to solve the YouTube signature, and
        # it gave 47.6 s and 47.1 s at four, 36.8 s and 36.0 s at eight
        # and 36.6 s and 36.1 s at twelve, all 12/12.
        #
        # Eight is the limit because twelve buys nothing: the wall time
        # is the same as eight, and every extra source is another node
        # process and another ffmpeg process on the machine. The earlier
        # "3/12 with ffmpeg exited with code 4294967274" was an artifact
        # of a benchmark that reused its output directories, so the
        # second run read the first run's files and reported them as its
        # own. With a clean directory per fetch there was no failure at
        # any level.
        partial = os.environ.get("DOCUMENTARY_PARTIAL_DOWNLOAD", "1") != "0"
        workers = int(os.environ.get("DOCUMENTARY_DOWNLOAD_CONCURRENCY", "16"))
        # The footage fingerprints of a source's windows are taken in the
        # background as soon as the source lands, so the grouping before
        # the shots reads them from the cache. footage imports this
        # module, so it is imported here and not at the top.
        from . import footage, window_index
        # A source spends 8 to 14 s waiting on its storyboard judgement,
        # which uses no line and no CPU. With one pool of `workers`, the
        # threads queued for a download slot held back the judgements
        # behind them and the last source was judged two minutes in. So
        # the pool has room for the 15 Flash channels on top, and
        # _DOWNLOAD_SLOTS still lets only `workers` sources fetch. A
        # pinpoint call waits 9 to 82 s on Flash the same way.
        if partial and (STORYBOARD or PINPOINT):
            workers += 15
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures=[pool.submit(fetch_partial if partial else fetch_and_probe,item) for item in tasks]
            # The local BBC library is searched and cut beside the fetches:
            # its windows are on disk in seconds, not minutes.
            if production.get("library") and not expansion_round:
                futures.append(pool.submit(_library_rows, sentences, out))
            for future in as_completed(futures):
                fetched = future.result()
                rows.extend(fetched)
                footage.prefetch(fetched)
                window_index.prefetch(fetched)
                # The contact frames feed describe_group, which a window
                # already classified by its pinpoint never reaches.
                prefetch_samples([r for r in fetched if not r.get("category")], out)
    unique = {r["id"]: r for r in rows}
    rows = sorted(unique.values(),key=lambda r:r["id"])
    source_policy_sha=sha(Path(__file__))
    identity = digest({"rows":[{k: r.get(k) for k in ("id", "sha256", "start", "end")} for r in rows],"source_policy_sha":source_policy_sha,"duration":timeline["audio_duration_sec"]})
    target = out / "catalog.json"
    if target.exists() and load(target).get("identity") == identity:
        return load(target)
    # Classify an initial diverse set, then expand only if the actual admitted pool is short.
    selected=[];remaining=list(rows);assets=[]
    # Pre-verified local 3D animations and assets enter catalog assets directly
    pre_verified = [r for r in rows if r.get("category") in ("3D", "PHOTO", "VIDEO") and r.get("usable")]
    assets.extend(pre_verified)
    remaining = [r for r in remaining if r["id"] not in {p["id"] for p in pre_verified}]

    # A bounded first pass keeps Flash classification proportional to the
    # material actually needed. If capacity is short, the existing rounds
    # below expand the shortlist in controlled batches.
    initial = min(120, max(48, math.ceil(float(timeline["audio_duration_sec"])*.5/10)*2))
    archive_photos_added = False
    from .planning import shot_length
    # "shot_seconds": "auto" counts the shots left after the fewest of them
    # are lengthened, as the runner will cut them (planning.shot_length).
    auto_length = production.get("shot_seconds") == "auto"
    for round_index in range(4):
        check_cancelled(out)
        admitted_vids = {origin_id(r) for r in assets if r.get("usable") and r.get("category") == "VIDEO"}
        batch = shortlist(remaining, initial * (2**round_index), admitted_origins=admitted_vids)
        if not batch: break
        selected.extend(batch); chosen = {r["id"] for r in batch}
        remaining = [r for r in remaining if r["id"] not in chosen]
        # Classify several adjacent candidates in one Flash request.
        batch_size = max(3, min(6, int(os.environ.get("DOCUMENTARY_SOURCE_BATCH_SIZE", "6"))))
        groups = [batch[i:i+batch_size] for i in range(0, len(batch), batch_size)]
        event(out, "inventory_round", round=round_index+1, raw_candidates=len(rows), selected=len(batch), remaining=len(remaining))
        with ThreadPoolExecutor(max_workers=max(1, int(os.environ.get("DOCUMENTARY_SOURCE_CONCURRENCY", "15")))) as pool:
            results = list(pool.map(lambda item: describe_group(item[1], round_index*10000+item[0], out), enumerate(groups)))
        assets.extend(r for group in results for r in group)
        capacity = pool_capacity(assets)
        event(out, "inventory_capacity", round=round_index+1, **capacity)
        unique_vids = len({origin_id(r) for r in assets if r.get("usable") and r.get("category") == "VIDEO"})
        total_sec = float(timeline.get("audio_duration_sec", 60.0))
        video_target_sec = total_sec * video_share
        estimated_video_shots = max(1, math.ceil(video_target_sec / 5.5))
        needed_unique_vids = max(2, math.ceil(estimated_video_shots / MAX_USES_PER_ORIGIN))
        available_vids = len({origin_id(r) for r in rows if r.get("kind") == "VIDEO"})
        needed_vids = min(needed_unique_vids, available_vids)
        available_photos = len({origin_id(r) for r in rows if r.get("kind") in ("PHOTO", "2D")})
        needed_photos = min(max(2, math.ceil(total_sec * photo_share / 6.0)), max(2, available_photos))
        needed_hook_sec = min(30.0, total_sec)
        # A photograph is used once in the film, so the photo pool has
        # to cover the photo share of the plan on its own. The delivered
        # run asked for 55 photo shots and had 11 usable photographs, so
        # the film printed one photograph seven times. The admission
        # check looked at video seconds and unique video sources and
        # never at the photo pool, so it stopped searching with the photo
        # pool far too small.
        photo_capacity = capacity["photos"] * MAX_USES_PER_MATERIAL
        # A film without photographs (wildlife) needs no photo pool.
        photo_target = max(2, math.ceil(total_sec * photo_share / 6.0)) if photo_share else 0
        photos_sufficient = photo_capacity >= photo_target
        # ARCHIVE PHOTO TOP-UP: when the photograph pool is short, real
        # archive photographs of the subject are fetched from the local
        # SearXNG instead of letting the film fall back on 3D. The
        # flow of the film is never changed by the size of the pool:
        # the plan is already written, and the pool only fills it.
        # An expansion round keeps the earlier catalog (runner._kept_catalog),
        # so photographs already fetched for the same query are in it; asking
        # again only described the same 37 photographs once more per round.
        topic_query = overview.get("topic", "") if isinstance(overview, dict) else str(overview)
        if not photos_sufficient and not archive_photos_added and expansion_round and _archive_query_done(out, topic_query):
            archive_photos_added = True
            event(out, "archive_photo_query_skipped", query=topic_query, reason="same query fetched in an earlier round")
        if not photos_sufficient and not archive_photos_added:
            archive_photos_added = True
            extra = fetch_archive_photos(topic_query, out,
                                         wanted=max(12, photo_target))
            if extra:
                remaining = list(remaining) + list(extra)
                event(out, "archive_photo_pool_added", count=len(extra),
                     query=topic_query)
                continue
        # Bounded fast admission: when video seconds and unique sources exceed requirement,
        # terminate immediately without burning extra rounds searching for non-existent photos.
        enough = ((unique_vids >= min(6, needed_vids) and capacity["video_seconds"] >= video_target_sec
                   and capacity["native_hook_seconds"] >= needed_hook_sec
                   and (photos_sufficient or round_index >= 1)) or round_index >= 1)
        # The fetched windows are on disk already and describing them costs
        # one Flash call per six. The shortlist takes one window per source
        # first, so a round that stopped on unique sources left two thirds
        # of the windows undescribed (Pantanal: 49 of 155), counted 46
        # clean cuts for 67 needed, and the runner searched and downloaded
        # a new round instead. The pool is described on while the clean
        # cuts, counted as the runner counts them, fall short.
        _regroup, cuts, needed_cuts = shot_length(timeline, {"assets": assets}, video_share * 100, auto_length)
        event(out, "inventory_cuts", round=round_index+1, clean_cuts=cuts, needed_cuts=needed_cuts)
        if (enough and cuts >= needed_cuts) or not remaining:
            break
    catalog = {"identity": identity,"source_policy_sha":source_policy_sha,"timeline_duration_sec":timeline["audio_duration_sec"], "topic": overview, "input_folder": str(folder), "documents": documents,
               "candidate_count":len(rows),"classified_count":len(assets),"unclassified_count":len(remaining),"assets":assets}
    save(target, catalog)
    return catalog
