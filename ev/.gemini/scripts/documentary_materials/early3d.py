"""Early 3D and ANIM production while the sources are still being fetched.

3D is behind DOCUMENTARY_EARLY_3D=1. A generated 3D shot needs no downloaded
source, yet nothing was produced until every source was downloaded and
classified and the plan was made (10-22 minutes). The scene scores of the
plan depend on the timeline only, so they are computed first, the shots
whose scene clearly wants 3D are locked to 3D (planning.select_early_3d),
and a small pool produces them during the sourcing. make_plan fixes the
same shots to 3D, and the main pipeline then finds their results already
made: a locked row is source-free (runner._source_free), so its identity
does not depend on the catalog and the normal reuse and validity checks
accept it.

ANIM (generated vox-style animation, anim.py) is started the same way
whenever the mix gives it time and G-Labs answers: one clip takes ~4
minutes, so it has to be made while the sources download, not at the end
of the queue. Its pool (DOCUMENTARY_ANIM_WORKERS, default 10) is not waited
for when the plan is made: a shot still in flight is waited for by the main
worker that reaches it (wait_anim), so no shot is made twice and the main
workers start at once.
"""

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import planning
from .control import set_context
from .io import digest, event, load, save
from .profiles import video_only

_POOLS = {}
SCORE_RETRY_SECONDS = float(os.environ.get("DOCUMENTARY_EARLY_SCORE_RETRY", "60"))
_ANIM = {}
_GUARD = threading.Lock()


def enabled():
    return os.environ.get("DOCUMENTARY_EARLY_3D") == "1"


def anim_wanted(targets):
    """The mix gives ANIM screen time (DOCUMENTARY_EARLY_ANIM=0 turns the early pool off)."""
    return (float((targets or {}).get("ANIM", 0)) > 0 and not video_only(targets)
            and os.environ.get("DOCUMENTARY_EARLY_ANIM", "1") != "0")


def _workers():
    # Two or three renders beside the downloads; never the full shot width.
    try:
        wanted = int(os.environ.get("DOCUMENTARY_EARLY_3D_WORKERS", "2"))
    except ValueError:
        wanted = 2
    return max(1, min(3, wanted))


def _lock_file(out):
    return Path(out) / "planning" / "early_3d.json"


def _anim_lock_file(out):
    return Path(out) / "planning" / "early_anim.json"


def _scores_key(out):
    path = Path(out) / "planning" / "scene_scores.json"
    return load(path).get("key") if path.exists() else None


def _locks(path, out, timeline):
    if not path.exists():
        return ()
    locks = load(path)
    if locks.get("timeline") != timeline["identity"] or locks.get("scores_key") != _scores_key(out):
        return ()
    return tuple(locks.get("locked") or ())


def locked_ids(out, timeline):
    """The 3D locks make_plan must honour, or () when there are none.

    They count only for the same timeline and the same stored scene scores
    they were chosen from, and only while the switch is on.
    """
    if not enabled():
        return ()
    return _locks(_lock_file(out), out, timeline)


def locked_anim_ids(out, timeline):
    """The ANIM locks make_plan must honour, by the same rules as 3D."""
    return _locks(_anim_lock_file(out), out, timeline)


class _Pool:
    def __init__(self):
        self.stopped = False
        self.executor = None
        self.thread = None


def start(timeline_path, out, targets):
    """Start scoring, locking and the background 3D/ANIM pools; returns at once."""
    if not enabled() and not anim_wanted(targets):
        return
    key = str(Path(out).resolve())
    with _GUARD:
        if key in _POOLS:
            return
        pool = _Pool()
        _POOLS[key] = pool
    pool.thread = threading.Thread(target=_setup, args=(pool, Path(timeline_path), Path(out), dict(targets)),
                                   name="early3d-setup", daemon=True)
    pool.thread.start()


def _setup(pool, timeline_path, out, targets):
    try:
        set_context(out)
        timeline = load(timeline_path)
        planned = planning.shots(timeline)
        # A scoring group that fell back on a Flash timeout stores nothing,
        # and without stored scores the early pools are skipped: on EP04 and
        # EP05 (2026-11-06) that put the first ANIM request 33-50 min into
        # stage 3 and left G-Labs idle until the shot queue was done. One
        # more try after a minute gets past a Flash straggler; a second
        # fallback skips the pools as before.
        for attempt in (1, 2):
            byscene = planning.score_scenes(timeline, out, store=True)
            if _scores_key(out) is not None or attempt == 2:
                break
            event(out, "early_3d_scores_retry", attempt=attempt, wait_seconds=SCORE_RETRY_SECONDS)
            time.sleep(SCORE_RETRY_SECONDS)
            with _GUARD:
                if pool.stopped:
                    return
        if _scores_key(out) is None:
            # A scoring group fell back on a timeout: nothing is stored and
            # nothing is locked; make_plan scores again as before.
            event(out, "early_3d_skipped", reason="scene scoring fell back; no stored scores")
            return
        planning._normalize_hook_scenes(byscene, planned)
        locked, rows = [], []
        if enabled():
            locked = planning.select_early_3d(planned, byscene, targets)
            rows = planning.locked_rows(planned, byscene, locked)
            save(_lock_file(out), {"timeline": timeline["identity"], "scores_key": _scores_key(out),
                                   "targets": targets, "locked": locked,
                                   "rows": {str(r["shot_id"]): digest(r) for r in rows}})
            event(out, "early_3d_locked", shots=locked, seconds=round(sum(r["duration_sec"] for r in rows), 2),
                  workers=_workers())
        anim_rows = []
        if anim_wanted(targets):
            from . import anim, runner
            if not anim.available():
                event(out, "early_anim_skipped", reason="G-Labs did not answer; ANIM shots are made after the plan")
            else:
                locked_anim = planning.select_early_anim(planned, byscene, targets, exclude=locked)
                anim_rows = planning.locked_rows(planned, byscene, locked_anim, "ANIM")
                save(_anim_lock_file(out), {"timeline": timeline["identity"], "scores_key": _scores_key(out),
                                            "targets": targets, "locked": locked_anim,
                                            "rows": {str(r["shot_id"]): digest(r) for r in anim_rows}})
                event(out, "early_anim_locked", shots=locked_anim,
                      seconds=round(sum(r["duration_sec"] for r in anim_rows), 2), workers=runner.ANIM_WORKERS)
                # One batched Flash call writes every locked shot's prompts;
                # each worker then reads its own.
                if anim_rows:
                    runner._anim_prompts(out, anim_rows, timeline)
        live_plan = {"shots": rows + anim_rows}
        with _GUARD:
            if pool.stopped:
                return
            if rows:
                pool.executor = ThreadPoolExecutor(max_workers=_workers(), thread_name_prefix="early3d")
                for row in rows:
                    pool.executor.submit(_work, row, out, timeline["audio_file"], live_plan, "3d")
            if anim_rows:
                from . import runner
                executor = ThreadPoolExecutor(max_workers=runner.ANIM_WORKERS, thread_name_prefix="earlyanim")
                _ANIM[str(Path(out).resolve())] = {
                    "executor": executor,
                    "futures": {row["shot_id"]: executor.submit(_work, row, out, timeline["audio_file"], live_plan, "anim")
                                for row in anim_rows}}
    except Exception as exc:
        # The early pool is an optimisation: when it fails, the normal
        # pipeline plans and produces every shot as before.
        try:
            event(out, "early_3d_failed", error=type(exc).__name__, detail=str(exc)[-600:])
        except Exception:
            pass


def _work(row, out, audio, live_plan, kind="3d"):
    from . import runner
    sid = row["shot_id"]
    set_context(out)
    runner.EARLY_LIVE_PLAN.plan = live_plan
    started = time.perf_counter()
    event(out, "early_%s_worker_started" % kind, shot=sid)
    try:
        try:
            result = runner._work_shot(row, [], audio, out)
        except Exception as exc:
            result = {"shot_id": sid, "status": "WORK_FAILED", "error": type(exc).__name__, "detail": str(exc)[-1000:]}
        save(Path(out) / "shots" / f"{sid:04d}" / "result.json", result)
        with runner.SELECTION_LOCK:
            runner._cache_result(out, sid, result)
        event(out, "early_%s_worker_finished" % kind, shot=sid, status=result.get("status"),
              elapsed_seconds=round(time.perf_counter() - started, 3))
    finally:
        runner._release_reservations(out, sid)
        runner.EARLY_LIVE_PLAN.plan = None


def stop_feeding(out):
    """No new early shot starts; the setup (scoring, locks) is waited for.

    Waiting for the setup keeps the locks and the stored scores settled
    before make_plan reads them. ANIM shots already in flight go on.
    """
    key = str(Path(out).resolve())
    with _GUARD:
        pool = _POOLS.get(key)
        if pool is None:
            return
        pool.stopped = True
        if pool.executor is not None:
            pool.executor.shutdown(wait=False, cancel_futures=True)
    if pool.thread is not None and pool.thread is not threading.current_thread():
        pool.thread.join()
    with _GUARD:
        entry = _ANIM.get(key)
    if entry is not None:
        entry["executor"].shutdown(wait=False, cancel_futures=True)


def join(out):
    """Stop feeding and wait for the early 3D shots in flight; idempotent.

    Early ANIM shots in flight are not waited for here (wait_anim, finish).
    """
    stop_feeding(out)
    with _GUARD:
        pool = _POOLS.pop(str(Path(out).resolve()), None)
    if pool is not None and pool.executor is not None:
        pool.executor.shutdown(wait=True)
        event(out, "early_3d_joined")


def wait_anim(out, shot_id):
    """Wait for the early ANIM worker of this shot, if one started it.

    True when that worker ran to its end, so the result on disk is its own.
    """
    with _GUARD:
        entry = _ANIM.get(str(Path(out).resolve()))
    future = (entry or {}).get("futures", {}).get(shot_id)
    if future is None or future.cancelled():
        return False
    try:
        future.result()
    except Exception:
        return False
    return True


def finish(out):
    """Wait for every early ANIM shot still in flight; idempotent."""
    stop_feeding(out)
    with _GUARD:
        entry = _ANIM.pop(str(Path(out).resolve()), None)
    if entry is not None:
        entry["executor"].shutdown(wait=True)
        event(out, "early_anim_joined")
