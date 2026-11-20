"""python -m unittest tests.test_autoresume (run from Engineered\\tools). No films, no bridge: fake launcher, fake logs."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import autoresume as ar  # noqa: E402
import supervisor as sv  # noqa: E402

NAME = "EP06_Greensburg_Kansas_2007"
T0 = 1_000_000.0


class Rig:
    def __init__(self, log_text=""):
        self.state, self.launched, self.lines, self.reports, self.restarts = {}, [], [], [], []
        self.log_text = log_text
        self.dir = tempfile.mkdtemp()
        ar.folder_for = lambda name, paths: "C:/in/" + name

    def tick(self, now, exits, runs=None, procs=None):
        ar.tick(self.state, now, runs if runs is not None else {"EP06": {"running": False, "name": NAME, "stage": 3, "end": now}},
                exits, {} if procs is None else procs, lambda f: self.log_text, {},
                lambda k, f, d: self.reports.append((k, f, d)),
                launcher=lambda folder, st: self.launched.append((folder, st)),
                restarter=lambda: self.restarts.append(1),
                log=lambda text, at: self.lines.append(text))


def ex(code, at, src="manual"):
    return {"film": "EP06", "code": code, "src": src, "at": at, "line": "x manual run exit %d" % code}


class T(unittest.TestCase):
    def test_stage3_requeue_after_wait(self):
        r = Rig()
        r.tick(T0, [ex(3, T0 - 1)])
        self.assertEqual(r.launched, [])
        self.assertIn("will requeue from stage 3 in 120 s (try 1/3", r.lines[0])
        r.tick(T0 + 60, [ex(3, T0 - 1)])
        self.assertEqual(r.launched, [])
        r.tick(T0 + 130, [ex(3, T0 - 1)])
        self.assertEqual(r.launched, [("C:/in/" + NAME, 3)])
        self.assertIn("queued from stage 3", r.lines[-1])
        r.tick(T0 + 200, [ex(3, T0 - 1)])  # waiting in run_when_free: no second launch
        self.assertEqual(len(r.launched), 1)
        r.tick(T0 + 900, [ex(3, T0 - 1)], runs={"EP06": {"running": True, "start": T0 + 800, "name": NAME, "stage": 3}})
        self.assertEqual(r.state["resume_pending"], {})

    def test_cap_stops_and_reports_once(self):
        r = Rig()
        t = T0
        for i in range(3):
            r.tick(t, [ex(3, t - 1)])
            r.tick(t + 1000, [ex(3, t - 1)])  # launch
            r.tick(t + 1100, [ex(3, t - 1)], runs={"EP06": {"running": True, "start": t + 1050, "name": NAME}})
            t += 2000
        self.assertEqual(len(r.launched), 3)
        r.tick(t, [ex(3, t - 1)])
        r.tick(t + 5000, [ex(3, t - 1)])
        self.assertEqual(len(r.launched), 3)
        self.assertEqual(len(r.reports), 1)
        self.assertEqual(r.reports[0][0], "autoresume_capped")
        self.assertIn("STOP, 3 requeues from stage 3", r.lines[-1])

    def test_not_resumable(self):
        for code in (1, 12, 127):
            r = Rig()
            r.tick(T0, [ex(code, T0 - 1)])
            r.tick(T0 + 5000, [ex(code, T0 - 1)])
            self.assertEqual(r.launched, [], code)
            self.assertIn("not resumable", r.lines[0])

    def test_queue_internal_retry_lines_skipped(self):
        r = Rig()
        e = ex(3, T0 - 1, src="queue")
        e["line"] = "x stopped in stage 3, resume from 3"
        r.tick(T0 + 5000, [e])
        self.assertEqual((r.launched, r.lines), ([], []))

    def test_transport_uses_reason_stage_then_run_stage(self):
        r = Rig("REASON transport stage 4: ConnectionResetError")
        r.tick(T0, [ex(10, T0 - 1)])
        r.tick(T0 + 200, [ex(10, T0 - 1)])
        self.assertEqual(r.launched[0][1], 4)
        r = Rig("nothing useful")
        r.tick(T0, [ex(10, T0 - 1)])
        r.tick(T0 + 200, [ex(10, T0 - 1)])
        self.assertEqual(r.launched[0][1], 3)  # run started at stage 3

    def test_duplicate_waits_then_restarts_bridge_only_when_idle(self):
        log = "REASON duplicate_job stage 3: This output already has an active production job"
        r = Rig(log)
        t = T0
        for i in range(3):
            r.tick(t, [ex(11, t - 1)])
            self.assertIn("in %d s" % (600, 1200, 1800)[i], r.lines[-1])
            r.tick(t + 2000, [ex(11, t - 1)])
            r.tick(t + 2100, [ex(11, t - 1)], runs={"EP06": {"running": True, "start": t + 2050, "name": NAME}})
            t += 4000
        self.assertEqual(len(r.launched), 3)
        # other film active: cap, no restart
        ar.recent_activity = lambda now, window=300: False
        r.tick(t, [ex(11, t - 1)], procs={"EP03_Nepal": 3})
        self.assertEqual((r.restarts, len(r.reports)), ([], 1))
        # idle machine: restart once and one more try
        r2 = Rig(log)
        r2.state = {"resume_counts": {"EP06|3|dup": 3}}
        r2.tick(T0, [ex(11, T0 - 1)], procs={})
        self.assertEqual(r2.restarts, [1])
        r2.tick(T0 + 60, [ex(11, T0 - 1)], procs={})
        self.assertEqual(len(r2.launched), 1)
        # activity in a film folder blocks the restart
        ar.recent_activity = lambda now, window=300: True
        r3 = Rig(log)
        r3.state = {"resume_counts": {"EP06|3|dup": 3}}
        r3.tick(T0, [ex(11, T0 - 1)], procs={})
        self.assertEqual((r3.restarts, len(r3.reports)), ([], 1))

    def test_listing_failure_never_launches(self):
        r = Rig()
        r.tick(T0, [ex(3, T0 - 1)])
        ar.tick(r.state, T0 + 500, {"EP06": {"running": False, "name": NAME}}, [ex(3, T0 - 1)], None, lambda f: "", {}, lambda *a: None,
                launcher=lambda *a: r.launched.append(a), log=lambda *a: None)
        self.assertEqual(r.launched, [])

    def test_prime_skips_history(self):
        r = Rig()
        ar.prime(r.state, [ex(3, T0 - 1)])
        r.tick(T0 + 5000, [ex(3, T0 - 1)])
        self.assertEqual((r.launched, r.lines), ([], []))

    def test_with_real_batch_log_parser(self):
        d = Path(tempfile.mkdtemp())
        (d / "batch.log").write_text(
            "2026-10-30 11:00:00 %s start (free RAM 5.0 GB)\n"
            "2026-10-30 12:00:00 %s stopped in stage 3, resume from 3\n"
            "2026-10-30 12:01:00 %s FAILED at stage 3\n" % (NAME, NAME, NAME), encoding="utf-8")
        old = sv.OUT
        sv.OUT = d
        try:
            runs, exits, _ = sv.parse_batch(sv.ts("2026-10-30 12:02:00"))
        finally:
            sv.OUT = old
        r = Rig()
        r.tick(sv.ts("2026-10-30 12:02:00"), exits, runs=runs)
        self.assertIn("will requeue from stage 3", r.lines[0])
        self.assertEqual(len(r.lines), 1)  # the queue's own "resume from 3" line is not a second incident


if __name__ == "__main__":
    unittest.main()
