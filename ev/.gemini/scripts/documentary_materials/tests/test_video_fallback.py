import unittest
from unittest import mock
from documentary_materials import runner


class VideoFallback(unittest.TestCase):
    def test_rejected_candidate_is_not_returned(self):
        assets = [{"id": f"clip{i}_000", "category": "VIDEO", "usable": True, "path": f"c{i}.mp4",
                   "start": 0, "end": 20, "origin": f"clip{i}"} for i in range(2)]
        shot = {"shot_id": 1, "narration": "x"}
        with mock.patch.object(runner, "probe", return_value={"format": {"duration": "20"}}), \
                mock.patch.object(runner, "is_range_file", return_value=False), \
                mock.patch.object(runner, "_film_talking_head", return_value=False), \
                mock.patch.object(runner, "_shot_narration", return_value="x"):
            first = runner._video_fallback_selection(assets, [], shot, 100, False)
            again = runner._video_fallback_selection(assets, [], shot, 100, False, rejected_ids={first[0]["id"]})
        self.assertTrue(first and again)
        self.assertNotEqual(first[0]["id"], again[0]["id"])


if __name__ == "__main__":
    unittest.main()
