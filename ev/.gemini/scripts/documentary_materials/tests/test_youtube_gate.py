"""The shared YouTube gate and caches, with no request to YouTube.

Run: python -m unittest tests.test_youtube_gate
yt-dlp's extractor is replaced by a fake; the one test that runs yt-dlp's
real download path serves a generated mp4 from a local HTTP server.
"""
import functools
import http.server
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path.home() / ".gemini" / "scripts"))
if "documentary_materials" not in sys.modules:
    spec = importlib.util.spec_from_file_location("documentary_materials", ROOT / "__init__.py",
                                                  submodule_search_locations=[str(ROOT)])
    sys.modules["documentary_materials"] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sys.modules["documentary_materials"])
from documentary_materials import sources, yt_cache, yt_gate  # noqa: E402


def _events(out):
    path = Path(out) / "events.jsonl"
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ytgate_"))
        self.saved = {k: getattr(yt_gate, k) for k in ("CACHE_DIR", "RPM", "BURST", "CONCURRENCY",
                                                       "BACKOFF_SECONDS", "BACKOFF_MAX_SECONDS",
                                                       "BLOCK_RETRIES", "MAX_WAIT_SECONDS")}
        yt_gate.CACHE_DIR = self.tmp / "cache"
        yt_gate.RPM, yt_gate.BURST, yt_gate.CONCURRENCY = 6000.0, 100, 8
        s = yt_gate._S
        s.update(tokens=100.0, stamp=time.monotonic(), active=0, until=0.0, streak=0, paused_at=0.0,
                 noticed=set(), disk=(None, 0.0), calls={})
        self.saved_allowed = sources.ALLOWED_CHANNELS
        self.saved_ydl = sources.yt_dlp.YoutubeDL
        self.film = self.tmp / "film"
        sources._pot_seen[0] = time.monotonic() + 3600    # no PO token server in tests
        (self.film / "sources").mkdir(parents=True)

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(yt_gate, k, v)
        yt_gate._S.update(until=0.0, streak=0, paused_at=0.0, disk=(None, 0.0))
        sources.ALLOWED_CHANNELS = self.saved_allowed
        sources.yt_dlp.YoutubeDL = self.saved_ydl
        shutil.rmtree(self.tmp, ignore_errors=True)


class FakeYDL:
    """Stands in for yt_dlp.YoutubeDL; answers from a table and counts the calls."""
    calls = []
    answers = {}

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def extract_info(self, url, download=False):
        FakeYDL.calls.append(url)
        answer = FakeYDL.answers.get(url, FakeYDL.answers.get("*"))
        if isinstance(answer, Exception):
            raise answer
        return answer(url) if callable(answer) else answer

    @staticmethod
    def sanitize_info(info, remove_private_keys=False):
        return dict(info)


class GateTest(_Base):
    def test_rate_limit_spaces_calls(self):
        yt_gate.RPM, yt_gate.BURST = 600.0, 1      # one call per 0.1 s
        yt_gate._S["tokens"] = 1.0
        started = time.monotonic()
        for _ in range(6):
            yt_gate.call("search", lambda: None)
        self.assertGreaterEqual(time.monotonic() - started, 0.45)

    def test_concurrency_cap_holds_across_threads(self):
        yt_gate.CONCURRENCY = 2
        live, peak, lock = [0], [0], threading.Lock()

        def work():
            with lock:
                live[0] += 1
                peak[0] = max(peak[0], live[0])
            time.sleep(0.05)
            with lock:
                live[0] -= 1
        threads = [threading.Thread(target=yt_gate.call, args=("metadata", work)) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(peak[0], 2)

    def test_refusal_pauses_everyone_and_retries_once(self):
        yt_gate.BACKOFF_SECONDS = 0.4
        tries = []

        def refused_once():
            tries.append(time.monotonic())
            if len(tries) == 1:
                raise RuntimeError("ERROR: [youtube] x: Sign in to confirm youâ€™re not a bot.")
            return "ok"
        self.assertEqual(yt_gate.call("metadata", refused_once, self.film), "ok")
        self.assertGreaterEqual(tries[1] - tries[0], 0.35)
        backoff = [e for e in _events(self.film) if e["stage"] == "youtube_backoff"]
        self.assertEqual(len(backoff), 1)
        self.assertEqual(backoff[0]["seconds"], 0.4)
        self.assertTrue((yt_gate.CACHE_DIR / "backoff.json").is_file())

    def test_backoff_grows_and_concurrent_refusals_count_once(self):
        yt_gate.BACKOFF_SECONDS, yt_gate.BLOCK_RETRIES = 0.2, 0
        began = time.time()
        first = yt_gate.report(RuntimeError("HTTP Error 429: Too Many Requests"), "search", self.film, began)
        # A call that started before the pause began is the same incident.
        same = yt_gate.report(RuntimeError("HTTP Error 429"), "search", self.film, began - 1)
        time.sleep(0.25)
        second = yt_gate.report(RuntimeError("not a bot"), "search", self.film)
        self.assertEqual((first, same, second), (0.2, 0.0, 0.4))

    def test_other_process_pause_is_honoured(self):
        yt_gate.CACHE_DIR.mkdir(parents=True)
        (yt_gate.CACHE_DIR / "backoff.json").write_text(json.dumps({"until": time.time() + 0.3}))
        started = time.monotonic()
        yt_gate.call("search", lambda: None, self.film)
        self.assertGreaterEqual(time.monotonic() - started, 0.25)
        self.assertTrue(any(e["stage"] == "youtube_paused" for e in _events(self.film)))

    def test_age_gate_is_not_a_refusal(self):
        self.assertFalse(yt_gate.throttled(RuntimeError("Sign in to confirm your age")))
        self.assertTrue(yt_gate.throttled(RuntimeError("Sign in to confirm you're not a bot")))


class SearchCacheTest(_Base):
    def setUp(self):
        super().setUp()
        FakeYDL.calls = []
        FakeYDL.answers = {}
        sources.yt_dlp.YoutubeDL = FakeYDL

    def test_short_query_is_not_sent_twice_and_repeat_is_cached(self):
        FakeYDL.answers["*"] = {"entries": [{"id": "a" * 11, "title": "x", "duration": 60}]}
        rows = sources._search_youtube("wolverine snow b-roll", 25)
        self.assertEqual(len(FakeYDL.calls), 1)          # three words: no identical fallback
        self.assertEqual(rows[0]["id"], "a" * 11)
        sources._search_youtube("wolverine snow b-roll", 25)
        self.assertEqual(len(FakeYDL.calls), 1)          # served by the cache
        sources._search_youtube("one two three four five six seven eight", 25)
        self.assertEqual(FakeYDL.calls[-1], "ytsearch25:one two three four five six")
        self.assertEqual(len(FakeYDL.calls), 3)          # a long query still gets its shorter retry

    def test_channel_search_is_cached(self):
        FakeYDL.answers["*"] = {"entries": [{"id": "b" * 11, "title": "Siberian tiger hunt", "duration": 300}]}
        first = sources._search_channel("UCxyz", "Siberian tiger", 5)
        second = sources._search_channel("UCxyz", "Siberian tiger", 5)
        self.assertEqual(first, second)
        self.assertEqual(len(FakeYDL.calls), 1)

    def test_channel_restricted_profile_skips_archives(self):
        asked = []
        saved = dict(sources._SEARCHERS)
        try:
            sources._SEARCHERS.update(commons=lambda t: asked.append("commons") or [],
                                      archive=lambda t: asked.append("archive") or [])
            FakeYDL.answers["*"] = {"entries": [{"id": "c" * 11, "title": "x", "duration": 60, "channel_id": "BBC"}]}
            sources.ALLOWED_CHANNELS = {"BBC"}
            result = sources.search("tiger", self.film / "searches" / "query_0",
                                    sites=("youtube", "commons", "archive"))
            self.assertEqual(asked, [])
            self.assertEqual([c["id"] for c in result["candidates"]], ["c" * 11])
            self.assertTrue(str(result["sites"]["commons"]).startswith("skipped"))
            sources.ALLOWED_CHANNELS = None
            sources.search("tiger", self.film / "searches" / "query_1", sites=("youtube", "commons", "archive"))
            self.assertEqual(sorted(asked), ["archive", "commons"])
        finally:
            sources._SEARCHERS.clear()
            sources._SEARCHERS.update(saved)


class ProbeCacheTest(_Base):
    def setUp(self):
        super().setUp()
        FakeYDL.calls = []
        FakeYDL.answers = {}
        sources.yt_dlp.YoutubeDL = FakeYDL

    def test_a_video_is_probed_once(self):
        url = "https://www.youtube.com/watch?v=" + "d" * 11
        FakeYDL.answers[url] = {"id": "d" * 11, "webpage_url": url, "title": "t", "duration": 600,
                                "formats": [{"ext": "mp4", "vcodec": "avc1", "height": 1080}]}
        a = sources.probe_source(url, self.film)
        (self.tmp / "other_film").mkdir()
        b = sources.probe_source(url, self.tmp / "other_film")
        self.assertEqual(a, b)
        self.assertEqual(len(FakeYDL.calls), 1)
        self.assertEqual(yt_gate.counts().get("metadata"), 1)

    def test_default_clients_first_mweb_only_as_fallback(self):
        seen = []
        url = "https://www.youtube.com/watch?v=" + "j" * 11
        mp4 = {"id": "j" * 11, "webpage_url": url, "title": "t", "duration": 600,
               "formats": [{"ext": "mp4", "vcodec": "avc1", "height": 1080, "protocol": "https", "url": "u"}]}

        class Clients(FakeYDL):
            def extract_info(self, u, download=False):
                clients = self.opts["extractor_args"]["youtube"]["player_client"]
                seen.append(list(clients))
                assert self.opts["remote_components"] == ["ejs:github"]
                assert self.opts["sleep_interval_requests"] == 1 and self.opts["extractor_retries"] == 1
                if clients == ["default"]:
                    raise RuntimeError("ERROR: [youtube] jjj: Requested format is not available")
                return mp4
        sources.yt_dlp.YoutubeDL = Clients
        sources._pot_seen[0] = time.monotonic()
        sources.probe_source(url, self.film)
        self.assertEqual(seen, [["default"], ["default", "mweb"]])
        seen.clear()
        sources.yt_dlp.YoutubeDL = type("Ok", (FakeYDL,), {"extract_info": lambda s, u, download=False:
                                                           seen.append(s.opts["extractor_args"]["youtube"]["player_client"]) or mp4})
        sources.probe_source("https://www.youtube.com/watch?v=" + "k" * 11, self.film)
        self.assertEqual(seen, [["default"]])

    def test_cookies_only_when_asked(self):
        saved = yt_gate.COOKIES_BROWSER
        try:
            yt_gate.COOKIES_BROWSER = ""
            self.assertNotIn("cookiesfrombrowser", sources._yt_common())
            yt_gate.COOKIES_BROWSER = "firefox:yt-dlp"
            self.assertEqual(sources._yt_common()["cookiesfrombrowser"], ("firefox", "yt-dlp", None, None))
        finally:
            yt_gate.COOKIES_BROWSER = saved

    def test_gone_video_is_remembered_but_a_refusal_is_not(self):
        gone = "https://www.youtube.com/watch?v=" + "e" * 11
        refused = "https://www.youtube.com/watch?v=" + "f" * 11
        FakeYDL.answers[gone] = RuntimeError("ERROR: [youtube] eee: Video unavailable")
        FakeYDL.answers[refused] = RuntimeError("ERROR: Sign in to confirm you're not a bot")
        yt_gate.BACKOFF_SECONDS, yt_gate.BLOCK_RETRIES = 0.01, 0
        for _ in range(2):
            with self.assertRaises(Exception):
                sources.probe_source(gone, self.film)
            with self.assertRaises(Exception):
                time.sleep(0.02)
                sources.probe_source(refused, self.film)
        self.assertEqual(FakeYDL.calls.count(gone), 1)
        # default, then the mweb fallback, on each of the two probes
        self.assertEqual(FakeYDL.calls.count(refused), 4)


def _clip(path, seconds, height=180):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "testsrc=size=%dx%d:rate=25:duration=%s" % (height * 16 // 9, height, seconds),
                    "-c:v", "libx264", "-g", "25", "-pix_fmt", "yuv420p", str(path)], check=True)


class WindowCacheTest(_Base):
    def setUp(self):
        super().setUp()
        self.fetched = []
        self.saved_dl = sources._ydl_download

        def fake_download(url, opts, out):
            template = str(opts["outtmpl"]).replace("%(section_number)03d", "{n:03d}").replace("%(ext)s", "mp4")
            for section in opts["download_ranges"](None, None):
                self.fetched.append((section["start_time"], section["end_time"]))
                _clip(template.format(n=section["index"]), section["end_time"] - section["start_time"])
            return {}, None
        sources._ydl_download = fake_download

    def tearDown(self):
        sources._ydl_download = self.saved_dl
        super().tearDown()

    def test_second_film_takes_shared_windows_and_survives_the_first_films_deletion(self):
        url = "https://www.youtube.com/watch?v=" + "g" * 11
        film_a, film_b = self.tmp / "A", self.tmp / "B"
        for f in (film_a, film_b, self.tmp / "C"):
            f.mkdir()
        files_a, payload_a = sources._download_windows(url, film_a, [(10, 18), (40, 48)], "g" * 11 + "_windows")
        self.assertEqual(len(self.fetched), 2)
        files_b, payload_b = sources._download_windows(url, film_b, [(40, 48), (70, 78)], "g" * 11 + "_windows")
        self.assertEqual(self.fetched[2:], [(70.0, 78.0)])            # only the new window
        self.assertTrue(os.path.samefile(files_a[1], files_b[0]))       # one file, two links
        self.assertEqual(payload_b["windows"][0]["cache"], payload_a["windows"][1]["cache"])
        self.assertEqual(sources.shared_window(files_b[0]), payload_b["windows"][0]["cache"])
        self.assertTrue(any(e["stage"] == "range_cache_hit" for e in _events(film_b)))
        shutil.rmtree(film_a)
        for w in payload_a["windows"]:
            self.assertTrue(Path(w["cache"]).is_file())
        self.assertTrue(files_b[0].is_file())
        # A third film asking for the first window again downloads nothing.
        sources._download_windows(url, self.tmp / "C", [(10, 18)], "g" * 11 + "_windows")
        self.assertEqual(len(self.fetched), 3)

    def test_lru_eviction_keeps_the_recent_and_the_films_links(self):
        url = "https://www.youtube.com/watch?v=" + "h" * 11
        files, payload = sources._download_windows(url, self.film, [(10, 18), (40, 48), (70, 78)], "h" * 11 + "_windows")
        entries = [Path(w["cache"]) for w in payload["windows"]]
        for i, entry in enumerate(entries):          # entry 0 oldest, entry 2 newest
            stamp = time.time() - 100 + i * 10
            os.utime(str(entry) + ".used", (stamp, stamp))
        removed = yt_cache.evict(cap=entries[1].stat().st_size + entries[2].stat().st_size, force=True)
        self.assertEqual(removed, 1)
        self.assertFalse(entries[0].exists())
        self.assertTrue(entries[2].exists())
        self.assertTrue(all(f.is_file() for f in files))       # the film keeps its links


class _Quiet(http.server.SimpleHTTPRequestHandler):
    """A file server that answers byte ranges, as the YouTube CDN does."""

    def log_message(self, *a):
        pass

    def do_GET(self):
        path = Path(self.translate_path(self.path))
        if not path.is_file():
            return self.send_error(404)
        blob = path.read_bytes()
        start, end = 0, len(blob) - 1
        wanted = self.headers.get("Range", "")
        if wanted.startswith("bytes="):
            a, _, b = wanted[6:].partition("-")
            start, end = int(a or 0), min(int(b) if b else len(blob) - 1, len(blob) - 1)
            self.send_response(206)
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, len(blob)))
        else:
            self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        try:
            self.wfile.write(blob[start:end + 1])
        except (ConnectionError, OSError):
            pass


class RealYtDlpPathTest(_Base):
    """yt-dlp's own section download from a stored extraction, no YouTube request."""

    def test_windows_from_stored_extraction(self):
        media = self.tmp / "media"
        media.mkdir()
        _clip(media / "v.mp4", 60, 1080)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(media)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            vid = "i" * 11
            url = "https://www.youtube.com/watch?v=" + vid
            info = {"id": vid, "title": "test", "ext": "mp4", "extractor": "youtube", "extractor_key": "Youtube",
                    "webpage_url": url, "duration": 60.0,
                    "formats": [{"format_id": "137", "ext": "mp4", "vcodec": "avc1.640028", "acodec": "none",
                                 "height": 1080, "width": 1920, "protocol": "http",
                                 "url": "http://127.0.0.1:%d/v.mp4" % server.server_address[1]}]}
            yt_cache.put_info(vid, info)
            sources.yt_dlp.YoutubeDL = self.saved_ydl
            files, payload = sources._download_windows(url, self.film, [(10, 18), (30, 38)], vid + "_windows")
            self.assertIsNotNone(files, _events(self.film))
            self.assertEqual([round(w["length_sec"]) for w in payload["windows"]], [8, 8])
            self.assertEqual(yt_gate.counts().get("metadata"), None)     # no extraction was made
            # The second film's partial hit fetches only window 1, under its own index.
            (self.tmp / "film2").mkdir()
            files2, payload2 = sources._download_windows(url, self.tmp / "film2", [(10, 18), (50, 58)], vid + "_windows")
            self.assertEqual([f.name for f in files2], [vid + "_windows_000.mp4", vid + "_windows_001.mp4"])
            self.assertTrue(os.path.samefile(files[0], files2[0]))
            self.assertEqual(round(payload2["windows"][1]["length_sec"]), 8)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
