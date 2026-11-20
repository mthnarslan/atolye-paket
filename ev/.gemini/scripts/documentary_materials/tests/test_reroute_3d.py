"""A 3D shot that failed review is not given 3D again: MOTION when it fits, else VIDEO, else the neighbour merge.

Run: python -m unittest tests.test_reroute_3d
The selector and the Codex plan review are replaced by fakes; nothing is sent anywhere.
"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path.home() / ".gemini" / "scripts"))
if "documentary_materials" not in sys.modules:
    spec = importlib.util.spec_from_file_location("documentary_materials", ROOT / "__init__.py",
                                                  submodule_search_locations=[str(ROOT)])
    sys.modules["documentary_materials"] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sys.modules["documentary_materials"])
from documentary_materials import planning as P  # noqa: E402


def shot(i, cat, sec, start):
    f0 = start * 25
    return {"shot_id": i, "scene_id": 1, "category": cat, "narration": "line %d" % i, "duration_sec": sec,
            "frame_start": f0, "frame_end": f0 + int(sec * 25), "timeline_start_sec": start, "timeline_end_sec": start + sec,
            "story_plan": {"scene_id": 1, "shot_id": i, "category": cat}}


def make_plan(motion=10, shots=None):
    shots = shots or [shot(1, "VIDEO", 5, 100), shot(2, "3D", 5, 105), shot(3, "3D", 8.8, 110), shot(4, "VIDEO", 5, 120)]
    p = {"targets": {"VIDEO": 40, "PHOTO": 10, "3D": 10, "CARD": 15, "MOTION": motion, "ANIM": 15}, "shots": shots,
         "identity": "x", "planned_percent": {}}
    return p


class Reroute(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp(prefix="reroute_"))
        (self.out / "planning").mkdir()
        self.saved = (P._planning_api, P.api, P.anim_possible)
        self.selection = {"failed": [], "donors": []}
        P._planning_api = lambda *a, **k: {"data": self.selection}
        P.api = lambda *a, **k: {"data": {"verdict": "PASS", "issues": [], "summary": ""}}
        P.anim_possible = lambda t: False
        self.catalog = {"assets": [{"id": "p%d" % i, "usable": True, "category": "PHOTO"} for i in range(5)]}

    def tearDown(self):
        P._planning_api, P.api, P.anim_possible = self.saved

    def repair(self, plan, ids):
        return P.repair_allocation(plan, self.catalog, self.out,
                                   [{"shot_id": i, "status": "REVIEW_REQUIRED", "problem": ""} for i in ids])

    def cats(self, plan):
        return {s["shot_id"]: s["category"] for s in plan["shots"]}

    def test_failed_3d_goes_to_motion_when_it_fits(self):
        plan, changed = self.repair(make_plan(), [2])
        self.assertEqual(self.cats(plan)[2], "MOTION")
        self.assertEqual(plan["shots"][1]["story_plan"]["category"], "MOTION")
        self.assertIn(2, changed)
        self.assertEqual(plan["failed_categories"]["2"], ["3D"])

    def test_long_3d_goes_to_video_not_back_to_3d(self):
        plan, changed = self.repair(make_plan(), [3])  # 8.8 s: no MOTION, no still
        self.assertEqual(self.cats(plan)[3], "VIDEO")

    def test_no_motion_in_mix_means_a_still_then_video(self):
        plan, _ = self.repair(make_plan(motion=0), [2])
        self.assertEqual(self.cats(plan)[2], "PHOTO")

    def test_selector_cannot_send_it_back_to_3d(self):
        self.selection = {"failed": [{"shot_id": 2, "category": "3D", "reason": "x"}], "donors": []}
        plan, _ = self.repair(make_plan(), [2])
        self.assertNotEqual(self.cats(plan)[2], "3D")

    def test_second_failure_never_returns_to_3d_and_ends_stuck(self):
        plan, _ = self.repair(make_plan(), [2])           # 3D -> MOTION
        seen = [self.cats(plan)[2]]
        for _ in range(4):
            plan, changed = self.repair(plan, [2])
            seen.append(self.cats(plan)[2])
        self.assertNotIn("3D", seen[0:])
        self.assertEqual(seen[:3], ["MOTION", "PHOTO", "VIDEO"])
        self.assertEqual(seen[-1], "VIDEO")               # nothing left: stays, goes to the neighbour merge
        self.assertEqual(changed, [])
        self.assertEqual(sorted(plan["failed_categories"]["2"]), ["3D", "MOTION", "PHOTO", "VIDEO"])

    def test_stuck_shot_is_left_unchanged_and_not_produced_again(self):
        plan = make_plan()
        plan["failed_categories"] = {"3": ["3D", "VIDEO"]}
        before = dict(plan["shots"][2])
        plan, changed = self.repair(plan, [3])
        self.assertEqual(changed, [])
        self.assertEqual(plan["shots"][2]["category"], before["category"])
        self.assertTrue((self.out / "material_plan.json").exists())

    def test_non_3d_failure_keeps_the_old_default_3d(self):
        plan, _ = self.repair(make_plan(), [1])           # VIDEO failed: first try is still 3D
        self.assertEqual(self.cats(plan)[1], "3D")
        self.assertEqual(plan["failed_categories"]["1"], ["VIDEO"])

    def test_reroute_helper(self):
        p = make_plan()
        self.assertEqual(P.reroute_from_failed(p, p["shots"][1], {"3D"}), "MOTION")
        self.assertEqual(P.reroute_from_failed(p, p["shots"][2], {"3D"}), "VIDEO")
        self.assertIsNone(P.reroute_from_failed(p, p["shots"][2], {"3D", "VIDEO"}))
        self.assertEqual(P.reroute_from_failed(p, p["shots"][1], {"VIDEO"}), "3D")

    def test_plan_review_stays_bound_to_the_plan(self):
        from documentary_materials.io import digest, load
        plan, _ = self.repair(make_plan(), [2])
        rev = load(self.out / "plan_review.json")
        self.assertEqual(rev["reviewed_plan_digest"], digest(P._review_payload(plan)))


if __name__ == "__main__":
    unittest.main()
