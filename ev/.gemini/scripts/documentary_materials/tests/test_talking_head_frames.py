"""The one-pass frame read gives the frames of one seek per sample, so the verdict cannot change.

Run: python -m unittest discover -s tests
Real shots: set DOCUMENTARY_TH_CLIPS to a folder of visual.mp4 copies.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
# io.py finds its sibling scripts beside the package; a worktree is not there.
sys.path.insert(0, str(Path.home() / ".gemini" / "scripts"))
if "documentary_materials" not in sys.modules:
    spec = importlib.util.spec_from_file_location("documentary_materials", ROOT / "__init__.py",
                                                  submodule_search_locations=[str(ROOT)])
    sys.modules["documentary_materials"] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sys.modules["documentary_materials"])
from documentary_materials import runner  # noqa: E402


def _times(span, samples=5):
    step = span / float(samples + 1)
    return [str(step * (i + 1)) for i in range(samples)]


def _duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip().split(",")[0])


class OnePassFrames(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.clips = []
        # Frame rates whose frame times do not land on round seconds, and one that does.
        for rate, seconds in (("25", 4.44), ("30000/1001", 5.3), ("24000/1001", 6.1)):
            path = Path(cls.tmp.name) / ("clip_%s.mp4" % rate.replace("/", "_"))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                            "testsrc2=size=1280x720:rate=%s:duration=%s" % (rate, seconds),
                            "-c:v", "libx264", "-g", "250", "-pix_fmt", "yuv420p", str(path)], check=True)
            cls.clips.append(path)
        folder = os.environ.get("DOCUMENTARY_TH_CLIPS")
        if folder:
            cls.clips += sorted(Path(folder).glob("*.mp4"))[:30]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_same_pixels_as_one_seek_per_sample(self):
        for clip in self.clips:
            times = _times(_duration(clip))
            seeks = [runner._frame_at(clip, t) for t in times]
            one = runner._frames_one_pass(clip, times)
            self.assertEqual(len(one), sum(f is not None for f in seeks), clip)
            for a, b in zip([f for f in seeks if f is not None], one):
                self.assertTrue(np.array_equal(a, b), "%s differs" % clip.name)

    def test_boundary_time_keeps_the_frame_on_it(self):
        # 4.44 s at 25 fps: the second sample is 1.48 s, a frame time, which -ss keeps.
        clip = self.clips[0]
        times = _times(4.44)
        self.assertTrue(np.array_equal(runner._frame_at(clip, times[1]), runner._frames_one_pass(clip, times)[1]))

    def test_time_past_the_end_has_no_frame(self):
        clip = self.clips[0]
        self.assertEqual(len(runner._frames_one_pass(clip, ["1.0", "99.0"])), 1)
        self.assertIsNone(runner._frame_at(clip, "99.0"))


if __name__ == "__main__":
    unittest.main()
