"""Media memory: decoder threads, job costs, the gate's budget, and the Flash
pre-screen before the render.

Run: python -m unittest discover -s tests
"""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path.home() / ".gemini" / "scripts"))
if "documentary_materials" not in sys.modules:
    spec = importlib.util.spec_from_file_location("documentary_materials", ROOT / "__init__.py",
                                                  submodule_search_locations=[str(ROOT)])
    sys.modules["documentary_materials"] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sys.modules["documentary_materials"])
from documentary_materials import code_identity, resources, runner  # noqa: E402
from documentary_materials.sources import samples  # noqa: E402

FIT = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf2f3ef"


class Threads(unittest.TestCase):
    def test_inserted_before_the_first_input(self):
        cmd = resources.with_threads(["ffmpeg", "-v", "error", "-ss", "3", "-i", "a.mp4", "-f", "null", "-"], 2)
        self.assertEqual(cmd[:3], ["ffmpeg", "-threads", "2"])
        self.assertEqual(cmd.count("-threads"), 1)

    def test_left_alone(self):
        own = ["ffmpeg", "-threads", "8", "-i", "a.mp4", "-f", "null", "-"]
        self.assertEqual(resources.with_threads(own, 2), own)
        probe = ["ffprobe", "-v", "error", "-i", "a.mp4"]
        self.assertEqual(resources.with_threads(probe, 2), probe)
        self.assertEqual(resources.with_threads(["ffmpeg", "-i", "a"], 0), ["ffmpeg", "-i", "a"])

    def test_output_threads_of_an_encoder_do_not_count(self):
        cmd = ["ffmpeg", "-i", "a.mp4", "-c:v", "libx264", "-threads", "2", "o.mp4"]
        self.assertEqual(resources.with_threads(cmd, 4)[:3], ["ffmpeg", "-threads", "4"])

    def test_same_pixels_with_fewer_decoder_threads(self):
        with tempfile.TemporaryDirectory() as tmp:
            clip = Path(tmp) / "c.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=50:duration=3",
                            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(clip)], check=True)
            md5 = []
            for threads in (None, 2):
                cmd = ["ffmpeg", "-v", "error", "-ss", "0.7", "-i", str(clip), "-vf", FIT + ",fps=25", "-f", "framemd5", "-"]
                if threads:
                    cmd = resources.with_threads(cmd, threads)
                md5.append(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
            self.assertGreater(md5[0].count("\n"), 50)
            self.assertEqual(md5[0], md5[1])


class JobKind(unittest.TestCase):
    def test_the_shot_path_commands(self):
        kinds = {
            "render": ["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", "s.mp4", "-frames:v", 93, "-an", "-vf", FIT,
                       "-c:v", "h264_nvenc", "-preset", "p1", "-pix_fmt", "yuv420p", "visual.mp4"],
            "photo": ["ffmpeg", "-loop", "1", "-i", "c.jpg", "-frames:v", 9, "-vf", "zoompan", "-c:v", "libx264", "v.mp4"],
            "mux": ["ffmpeg", "-v", "error", "-y", "-i", "v.mp4", "-ss", "3", "-i", "a.wav", "-map", "0:v:0", "-map", "1:a:0",
                    "-t", "3", "-c:v", "copy", "-c:a", "aac", "scene.mp4"],
            "concat": ["ffmpeg", "-f", "concat", "-safe", "0", "-i", "l.txt", "-an", "-c:v", "copy", "v.mp4"],
            "verify": ["ffmpeg", "-v", "error", "-xerror", "-i", "scene.mp4", "-f", "null", "-"],
            "samples": ["ffmpeg", "-v", "error", "-y", "-i", "v.mp4", "-vf", "select", "-pix_fmt", "yuvj420p", "r_%03d.jpg"],
            "band": ["ffmpeg", "-v", "error", "-ss", "1", "-i", "s.mp4", "-frames:v", "1", "-vf", "crop", "-f", "rawvideo", "-"],
            "nvenc_probe": ["ffmpeg", "-f", "lavfi", "-i", "color", "-frames:v", "1", "-c:v", "h264_nvenc", "-f", "null", "-"],
            "not_ffmpeg": ["node", "x.js"],
        }
        want = {"render": "heavy", "photo": "heavy", "mux": "copy", "concat": "copy", "verify": "decode",
                "samples": "decode", "band": "decode", "nvenc_probe": "heavy", "not_ffmpeg": "heavy"}
        self.assertEqual({k: resources.job_kind(v) for k, v in kinds.items()}, want)


class Gate(unittest.TestCase):
    def test_a_settled_job_is_not_counted_twice(self):
        gate = resources.MemoryGate(per_unit_mb=300, ceiling=12)
        clock = [1000.0]
        with mock.patch.object(resources, "free_memory_mb", return_value=1800), \
                mock.patch.object(resources.time, "monotonic", side_effect=lambda: clock[0]):
            # The first job is held by another thread (a nested job on the same thread is admitted by design).
            self.assertTrue(gate._admit(300, False, "first"))
            # 600 MB of budget, 300 held by a job whose memory is not in the free memory yet.
            self.assertTrue(gate._admit(300, False, "second"))
            self.assertFalse(gate._admit(300, False, "third"))
            clock[0] += resources.RAMP_SECONDS
            # Both jobs now show in the free memory (still read as 1800 here, the
            # worst case): their charges come back and the third one fits.
            self.assertTrue(gate._admit(300, False, "third"))
            gate._release(300, False, "second"); gate._release(300, False, "third")
            gate._release(300, False, "first")
        self.assertEqual((gate._busy, gate._used_mb, gate._started), (0, 0, {}))

    def test_one_job_runs_under_the_reserve(self):
        gate = resources.MemoryGate(per_unit_mb=300)
        with mock.patch.object(resources, "free_memory_mb", return_value=100):
            self.assertTrue(gate._admit(300, False, "a"))
            self.assertFalse(gate._admit(80, True, "b"))


class ShotIdentity(unittest.TestCase):
    def test_prompt_literals_unchanged(self):
        # The selection and review prompts are part of every shot's identity;
        # the pre-render precheck must not change them (a changed hash makes
        # every film produce its shots again). Update only on purpose.
        self.assertEqual(code_identity.literals("runner.py", *runner._SHOT_PROMPT_CODE),
                         "888a5de161e5ad2ded5640a54901564eea546dbfb6f84a0e3a484075de028b20")

    def test_video_and_photo_shot_code_unchanged(self):
        # darbogaz_1107: _shot_code is now the narrow key; the old whole-module key (_shot_code_wide) must stay equal to what finished shots were stamped with.
        # 2026-11-05: changed on purpose (video fallback honours rejected_ids, c4f38ff).
        self.assertEqual(runner._shot_code_wide("VIDEO"), "257dc5a9dad0d5a440c35bb856528ca00c06c82407b0e325de211961ea91b1e0")
        self.assertEqual(runner._shot_code_wide("PHOTO"), "170712f583d420da84aeca55458a1ce001b8a897ad2b2c4a73071314b3ef5d37")


class PrerenderPrecheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.clip = Path(cls.tmp.name) / "source.mp4"
        # A 4:3 source at 30 fps: the fit pads it, and its frame times are not on the 25 fps grid.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=960x720:rate=30:duration=8",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(cls.clip)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_tiles_are_the_frames_of_the_render(self):
        shot = {"shot_id": 7, "frame_start": 0, "frame_end": 113, "duration_sec": 4.52}
        asset = {"category": "VIDEO", "id": "x", "path": str(self.clip), "start": 1.3, "end": 7.9}
        folder = Path(self.tmp.name) / "shot"; folder.mkdir()
        board, tiles = runner._prerender_board(shot, asset, folder)
        self.assertTrue(Path(board).is_file())
        # The render's chain, encoded losslessly, then the review's own sampling.
        visual = folder / "visual.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.3", "-i", str(self.clip), "-frames:v", "113", "-an",
                        "-vf", FIT + ",setsar=1,fps=25", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", str(visual)],
                       check=True)
        times = [min(t, 4.52 - .04) for t in [0.04, 1.0, 2.0, 3.0, 4.0, 4.52 - .08]]
        post = samples(visual, times, [folder / ("review_%d.jpg" % i) for i in range(len(times))])
        self.assertEqual(len(tiles), len(post))
        for a, b in zip(tiles, post):
            x = np.asarray(Image.open(a).convert("RGB"), np.float32)
            y = np.asarray(Image.open(b).convert("RGB"), np.float32)
            self.assertEqual(x.shape, y.shape)
            self.assertLess(float(np.abs(x - y).mean()), 3.0, a)

    def test_no_board_when_the_render_would_repair_the_range(self):
        shot = {"shot_id": 8, "frame_start": 0, "frame_end": 100, "duration_sec": 4.0}
        short = {"category": "VIDEO", "id": "x", "path": str(self.clip), "start": 1.0, "end": 3.0}
        self.assertIsNone(runner._prerender_board(shot, short, Path(self.tmp.name)))

    def test_refused_candidate_is_not_rendered_and_keeps_one_flash_look(self):
        shot = {"shot_id": 9, "category": "VIDEO", "frame_start": 0, "frame_end": 100, "duration_sec": 4.0}
        asset = {"category": "VIDEO", "id": "x", "path": str(self.clip), "start": 1.0, "end": 7.0}
        out = Path(self.tmp.name) / "run"; folder = out / "shots" / "0009"; folder.mkdir(parents=True)
        calls = []
        refuse = {"shows": "a test card", "visual_fit": "FAIL", "reason": "unrelated"}
        with mock.patch.object(runner, "_flash_precheck", side_effect=lambda *a, **k: calls.append(a[2]) or refuse), \
                mock.patch.object(runner, "_reserve_sources"), mock.patch.object(runner, "render") as render, \
                mock.patch.object(runner, "event"):
            rendered = runner._render_shot_artifact(shot, asset, "a.wav", folder, out, {}, [], False, "id")
        render.assert_not_called()
        self.assertEqual(len(calls), 1, rendered)
        artifact = rendered["artifact"]
        self.assertFalse(artifact["rendered"])
        self.assertIsNone(artifact["visual_path"])
        self.assertFalse(runner._delivered_talking_head(artifact, shot))
        # _work_shot's post-render steps on this record: the tiles Flash saw, no
        # detail frame, and the answer given before the render, not a second call.
        tiles = runner._picture_reader(rendered, runner.samples)("ignored", [], [])
        self.assertEqual(tiles, rendered["precheck"]["tiles"])
        self.assertIsNone(runner._picture_reader(rendered, runner.sample)(None, 1.0, "x"))
        self.assertIs(runner._precheck_or(rendered["precheck"], None)(), rendered["precheck"])
        self.assertIs(runner._precheck_or(None, len), len)

    def test_switched_off_and_other_categories_go_the_old_way(self):
        shot = {"shot_id": 9, "frame_start": 0, "frame_end": 100, "duration_sec": 4.0}
        out = Path(self.tmp.name) / "run2"
        with mock.patch.object(runner, "_flash_precheck") as flash:
            self.assertIsNone(runner._prerender_precheck(shot, {"category": "PHOTO", "path": "p.jpg"}, out, out))
            with mock.patch.object(runner, "PRERENDER_PRECHECK", False):
                self.assertIsNone(runner._prerender_precheck(
                    shot, {"category": "VIDEO", "path": str(self.clip), "start": 1, "end": 7}, out, out))
        flash.assert_not_called()


if __name__ == "__main__":
    unittest.main()
