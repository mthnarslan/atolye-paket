"""Windows native bridge for Dify visual flow.

Dify runs in Linux containers. The documentary pipeline uses Windows paths,
msvcrt locks, Sopro CUDA, Whisper CUDA, and NVENC, so this HTTP bridge executes
the stages directly on native Windows while exposing granular stage status to the UI.
"""
from __future__ import annotations

import json
import inspect
import os
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

# Ensure logs work under pythonw where sys.stdout is None
LOG_DIR = Path(r"C:\Users\meteh\.gemini\scripts")
if sys.stdout is None:
    sys.stdout = open(LOG_DIR / "bridge.log", "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = open(LOG_DIR / "bridge.err.log", "a", encoding="utf-8", buffering=1)

SCRIPTS = Path(r"C:\Users\meteh\.gemini\scripts")
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

HOST = "0.0.0.0"
PORT = int(os.environ.get("DOCUMENTARY_BRIDGE_PORT", "8099"))
BRIDGE_FILE = Path(__file__).resolve()
# The source of the running bridge, kept so a change to this file can be
# detected without a restart.
try:
    _BRIDGE_SOURCE = BRIDGE_FILE.read_text(encoding="utf-8")
except Exception:
    _BRIDGE_SOURCE = ""


def _jsonable(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "data") and isinstance(value.data, dict):
        return _jsonable(value.data)
    return value


def _progress(message):
    print(message, flush=True)


# One reload at a time: four films starting stage 1 together reloaded the
# voice modules from four threads, and importlib.invalidate_caches raised
# KeyError on the bridge's own path (CONC_1..4, 2026-10-27). Kept across the
# bridge's own reload.
import threading as _threading
_RELOAD_LOCK = globals().get("_RELOAD_LOCK") or _threading.RLock()


def _one_at_a_time(fn):
    def run(*args, **kwargs):
        with _RELOAD_LOCK:
            return fn(*args, **kwargs)
    run.__name__, run.__doc__ = fn.__name__, fn.__doc__
    return run


@_one_at_a_time
def _reload_material_modules():
    """Refresh the material modules so code changes take effect without a
    bridge restart.

    The list is discovered, not written by hand. A hand-written list
    goes stale the moment a module is added: render_stage was left out
    once, so the delivery report kept running the old code even though
    the file on disk had changed. Discovering the package means a new
    module is never forgotten.
    """
    import importlib
    importlib.invalidate_caches()
    # documentary_file_io goes first. The modules below bind its
    # functions at import time ("from documentary_file_io import
    # replace_posix"), so reloading them before the shared layer would
    # leave them holding the previous code.
    if "documentary_file_io" in sys.modules:
        try:
            importlib.reload(sys.modules["documentary_file_io"])
        except Exception:
            pass
    names = [name for name in sys.modules
             if name.startswith("documentary_materials.")
             or name == "adaptive_governor"]
    for module_name in names:
        # The registry of active runs is the one module that must not be
        # reloaded: a reload empties it, and the guard that stops a
        # second production pass on the same output stops working.
        # Measured on the live run, the second pass put 15 workers on
        # top of the 15 the first one still had, and the run took 2885
        # seconds against a 1200 second budget.
        #
        # The scan cache is the same kind of module: a reload empties
        # the motion and talking head caches, and the next stage
        # request measures the same candidates again. Measured on the
        # live run, the hook scan of 4622 video candidates cost about
        # 1774 seconds and the reload in front of the next request threw
        # that away, so the second run paid about 1583 seconds more for
        # the same answer.
        if module_name in ("documentary_materials.run_registry",
                           "documentary_materials.scan_cache"):
            continue
        module = sys.modules.get(module_name)
        if module is None:
            continue
        try:
            importlib.reload(module)
        except Exception:
            pass


def _bridge_source_changed():
    """True when this file on disk differs from the one that is running.

    The bridge is a long running process. Without this check, a change
    to the bridge itself stays invisible until it is restarted, and the
    restart is not always possible: the process may be owned by someone
    else, or work may be in flight. Comparing the running source with
    the file on disk lets the bridge pick up its own change.
    """
    try:
        running = _BRIDGE_SOURCE
        on_disk = BRIDGE_FILE.read_text(encoding="utf-8")
    except Exception:
        return False
    return running != on_disk


def _reload_bridge_itself():
    """Re-read this file so a change to the bridge takes effect.

    The module is executed in a fresh namespace and its globals are
    copied over this one, so the running server keeps serving while the
    new code takes over. The module-level constants (host, port) are
    left alone: changing them would mean a different server.

    The handler class is the part that has to be pushed into the
    running server as well. The server bound the class object when it
    started, so copying the globals left the old request handler
    serving. Measured on the live run: a new endpoint on this file
    answered 404 after a reload, and a fix to the material stage never
    reached the run, because the running bridge was still the old
    code. The server keeps the same socket and the same port, so the
    swap is invisible to the client.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("documentary_native_bridge", BRIDGE_FILE)
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    # The running server is not in the file, so it is carried over by
    # hand. The freshly executed module has no server of its own.
    _live_server = globals().get("SERVER")
    for key, value in fresh.__dict__.items():
        if key.startswith("__") or key in ("BRIDGE_FILE",):
            continue
        globals()[key] = value
    if _live_server is not None:
        globals()["SERVER"] = _live_server
    # The running source is now the one on disk. Without this the bridge
    # would think it is stale on every single request and reload itself
    # over and over.
    globals()["_BRIDGE_SOURCE"] = fresh.__dict__.get("_BRIDGE_SOURCE", "")
    # Push the new handler into the server that is already listening.
    try:
        _server = globals().get("SERVER")
        if _server is not None and "Handler" in globals():
            _server.RequestHandlerClass = globals()["Handler"]
    except Exception:
        pass
    return True


@_one_at_a_time
def _reload_voice_modules():
    """Refresh the voice modules so code changes take effect without a
    bridge restart.

    The list is discovered, for the same reason as in
    _reload_material_modules: a hand-written list goes stale as soon as
    a module is added.
    """
    import importlib
    importlib.invalidate_caches()
    if "documentary_file_io" in sys.modules:
        try:
            importlib.reload(sys.modules["documentary_file_io"])
        except Exception:
            pass
    # sopro_voice_client too: its wait limits were raised for a loaded GPU
    # and never reached the running bridge (TOPIC_6, 2026-10-26).
    names = [name for name in sys.modules
             if name.startswith("documentary_voice_")
             or name in ("adaptive_governor", "sopro_voice_client")]
    for module_name in names:
        module = sys.modules.get(module_name)
        if module is not None:
            try:
                importlib.reload(module)
            except Exception:
                pass


def run_stage_1_1(folder: str, dry_run: bool = False):
    folder_path = Path(folder).expanduser().resolve(strict=True)
    if dry_run:
        return {"status": "DRY_RUN", "step": "1.1_scan", "folder": str(folder_path)}
    _reload_voice_modules()
    import documentary_voice_engine as engine
    started = time.perf_counter()
    out = engine.voice_output_dir(folder_path)
    out.mkdir(parents=True, exist_ok=True)
    engine.save_json(out / "voice_source.json", {"input_folder": str(folder_path)})
    inventory_sig = engine.source_inventory_signature(folder_path)
    scan = engine.scan_material_folder(folder_path)
    scan["source_inventory_sha256"] = inventory_sig
    engine.save_json(out / "source_selection.json", scan)
    elapsed = time.perf_counter() - started
    budget = engine.budget_report("1.1_scan", elapsed)
    engine.save_json(out / "voice_progress.json", {
        "status": "SCANNED", "step": "1.1_scan",
        "script_path": scan["script_path"],
        "ref_audio_path": scan["ref_audio_path"],
        "budget": budget,
    })
    return _jsonable({
        "status": "PASS",
        "step": "1.1 • Flash Klasör Taraması",
        "folder": str(folder_path),
        "script_path": scan["script_path"],
        "ref_audio_path": scan["ref_audio_path"],
        "script_preview": scan.get("raw_text", "")[:200] + "...",
        "selection_reason": scan.get("decision", {}).get("reason", ""),
        "elapsed_seconds": round(elapsed, 3),
        "budget": budget,
    })


def run_stage_1_2(folder: str, dry_run: bool = False):
    folder_path = Path(folder).expanduser().resolve(strict=True)
    if dry_run:
        return {"status": "DRY_RUN", "step": "1.2_prepare", "folder": str(folder_path)}
    _reload_voice_modules()
    import documentary_voice_engine as engine
    started = time.perf_counter()
    out = engine.voice_output_dir(folder_path)
    out.mkdir(parents=True, exist_ok=True)
    scan = engine.load_json(out / "source_selection.json")
    if not scan:
        scan = engine.scan_material_folder(folder_path)
        scan["source_inventory_sha256"] = engine.source_inventory_signature(folder_path)
        engine.save_json(out / "source_selection.json", scan)
    plan = _narration_plan(engine, out, scan)
    (out / "narration.txt").write_text(plan["narration"], encoding="utf-8")
    elapsed = time.perf_counter() - started
    budget = engine.budget_report("1.2_prepare", elapsed)
    engine.save_json(out / "voice_progress.json", {
        "status": "PREPARED", "step": "1.2_prepare",
        "chunk_count": len(plan["chunks"]),
        "language": plan.get("language", "en"),
        "budget": budget,
    })
    return _jsonable({
        "status": "PASS",
        "step": "1.2 • Flash Metin Cümleleme & Planlama",
        "chunk_count": len(plan["chunks"]),
        "language": plan.get("language", "en"),
        "narration_file": str(out / "narration.txt"),
        "sample_chunk": plan["chunks"][0] if plan.get("chunks") else "",
        "elapsed_seconds": round(elapsed, 3),
        "budget": budget,
    })


def _narration_plan(engine, out, scan):
    """The cached narration plan, rebuilt when the script or parser changed."""
    plan_key = engine.narration_plan_key(scan)
    previous = engine.load_json(out / "narration_plan.json")
    if previous and previous.get("key") == plan_key:
        return previous["plan"]
    if scan.get("decision", {}).get("autonomous_bootstrap") or "SES / ANLATIM" in scan["raw_text"].upper():
        plan = engine.prepare_narration_bootstrap(scan["raw_text"])
    else:
        plan = engine.prepare_narration(scan["raw_text"])
    engine.save_json(out / "narration_plan.json", {"key": plan_key, "plan": plan})
    return plan


def run_stage_1_3(folder: str, dry_run: bool = False):
    folder_path = Path(folder).expanduser().resolve(strict=True)
    if dry_run:
        return {"status": "DRY_RUN", "step": "1.3_synthesize", "folder": str(folder_path)}
    _reload_voice_modules()
    import documentary_voice_engine as engine
    started = time.perf_counter()
    out = engine.voice_output_dir(folder_path)
    scan = engine.load_json(out / "source_selection.json")
    if not scan:
        scan = engine.scan_material_folder(folder_path)
        scan["source_inventory_sha256"] = engine.source_inventory_signature(folder_path)
        engine.save_json(out / "source_selection.json", scan)
    plan = _narration_plan(engine, out, scan)
    chunks = list(plan["chunks"])
    options = {}
    manifest = engine.generate_full_voiceover(
        chunks, scan["ref_audio_path"], out, plan["language"], _progress, chunk_options=options
    )
    manifest["approved_chunks"] = plan["chunks"]
    manifest["plan_key"] = engine.narration_plan_key(scan)
    manifest["chunk_options"] = options
    script_hash = engine.file_hash(scan["script_path"])
    inventory_sig = engine.source_inventory_signature(folder_path)
    manifest.update(
        model=engine.MODEL, version=engine.VERSION,
        script_path=scan["script_path"], script_sha256=script_hash,
        selection_reason=scan["decision"].get("reason", ""),
        input_folder=str(folder_path), source_inventory_sha256=inventory_sig
    )
    (out / "narration.txt").write_text("\n".join(chunks), encoding="utf-8")
    manifest["narration_sha256"] = engine.file_hash(out / "narration.txt")
    engine.save_json(out / "voice_manifest.json", manifest)
    elapsed = time.perf_counter() - started
    budget = engine.budget_report("1.3_synthesize", elapsed)
    engine.save_json(out / "voice_progress.json", {
        "status": "GENERATED", "step": "1.3_synthesize",
        "output_file": manifest["output_file"],
        "duration_sec": manifest["raw_duration_sec"],
        "budget": budget,
    })
    return _jsonable({
        "status": "PASS",
        "step": "1.3 • Sopro GPU Ses Sentezi",
        "output_file": manifest["output_file"],
        "duration_sec": manifest["raw_duration_sec"],
        "total_chunks": manifest["total_chunks"],
        "speed_factor": manifest.get("speed_factor"),
        "synthesis_time_sec": manifest.get("synthesis_time_sec"),
        "elapsed_seconds": round(elapsed, 3),
        "budget": budget,
    })


def run_stage_1_4(folder: str, dry_run: bool = False):
    folder_path = Path(folder).expanduser().resolve(strict=True)
    if dry_run:
        return {"status": "DRY_RUN", "step": "1.4_audit", "folder": str(folder_path)}
    _reload_voice_modules()
    import documentary_voice_engine as engine
    import documentary_voice_audit as auditor
    import documentary_voice_repair as repair
    started = time.perf_counter()
    manifest, audit = repair.run_with_repair(engine, auditor, folder_path, _progress)
    elapsed = time.perf_counter() - started
    budget = engine.budget_report("1.4_audit", elapsed)
    review = audit.get("gemini_audio") or {}
    out = engine.voice_output_dir(folder_path)
    engine.save_json(out / "voice_progress.json", {
        "status": "SUCCESS" if audit.get("next_step_allowed") else audit.get("verdict", "UNVERIFIED"),
        "step": "1.4_audit",
        "audit_verdict": audit.get("verdict"),
        "next_step_allowed": audit.get("next_step_allowed", False),
        "output_file": manifest.get("output_file"),
        "budget": budget,
    })
    return _jsonable({
        "status": audit.get("verdict", "UNVERIFIED"),
        "step": "1.4 • Flash 3.8 Denetim & Onarım",
        "verdict": audit.get("verdict"),
        "next_step_allowed": audit.get("next_step_allowed", False),
        "voice_output_dir": str(engine.voice_output_dir(folder_path)),
        "output_file": manifest.get("output_file"),
        "duration_sec": manifest.get("raw_duration_sec"),
        "repair_rounds": audit.get("repair_rounds", 0),
        "segment_count": review.get("segment_count"),
        "integrity_defects": audit.get("integrity_defects"),
        "summary": audit.get("summary", ""),
        "elapsed_seconds": round(elapsed, 3),
        "budget": budget,
    })


FILM_SETTINGS = "film_settings.json"


def _film_profile(folder_path: Path, requested=None) -> str:
    """The film's production profile ("default", "wildlife").

    A /run body may name it on any stage; it is kept in the film's
    film_settings.json beside the voice output, so a later stage or a
    restart that sends no profile uses the same one. Stage 3 also writes it
    into the material run's settings.json, which steps 3 and 4 read.
    """
    import documentary_voice_engine as engine
    from documentary_materials.profiles import get

    path = engine.voice_output_dir(folder_path) / FILM_SETTINGS
    stored = (engine.load_json(path) or {}) if path.is_file() else {}
    if requested is None:
        return get(stored.get("profile"))["name"]
    name = get(requested)["name"]
    if stored.get("profile") != name:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**stored, "profile": name}, ensure_ascii=False, indent=2), encoding="utf-8")
    return name


def _material_profile(mat_out: Path) -> str:
    """The profile the material in mat_out was made under (older runs: default)."""
    import documentary_voice_engine as engine

    return (engine.load_json(mat_out / "settings.json") or {}).get("profile") or "default"


def _other_voice_active(own_dir, fresh_s=600):
    """True while another film is still making or checking its voice.

    The GPU voice service is shared: stopping it when one film's voice
    passes killed it under the next film mid-sentence (19:41 and 20:02 on
    5 Nov), and each restart cost a model load and a client retry.
    """
    own = Path(own_dir).resolve()
    for prog in own.parent.glob("*/voice_progress.json"):
        if prog.parent.resolve() == own:
            continue
        try:
            if time.time() - prog.stat().st_mtime > fresh_s:
                continue
            status = json.loads(prog.read_text(encoding="utf-8")).get("status", "")
        except (OSError, ValueError):
            continue
        if status not in ("SUCCESS", "PASS", "FAILED", "FAIL", "BLOCKED"):
            return True
    return False


def run_stage(stage: int, folder: str, dry_run: bool = False, preview_seconds: int = 0, profile=None):
    folder_path = Path(folder).expanduser().resolve(strict=True)
    if dry_run:
        return {"status": "DRY_RUN", "stage": stage, "folder": str(folder_path)}
    profile = _film_profile(folder_path, profile)

    if stage in (1, 2):
        _reload_voice_modules()

    started = time.perf_counter()
    if stage == 1:
        import documentary_voice_engine as engine
        import documentary_voice_audit as auditor
        import documentary_voice_repair as repair

        manifest, audit = repair.run_with_repair(engine, auditor, folder_path, _progress)
        import sopro_voice_client
        # Pocket (CPU, ~2 GB) stays up: another film may be voicing on it
        # right now, and it holds no GPU memory the shot workers need.
        if (audit.get("next_step_allowed") and sopro_voice_client.ENGINE != "pocket"
                and not _other_voice_active(engine.voice_output_dir(folder_path))):
            if sopro_voice_client.ENGINE == "chatterbox":
                sopro_voice_client.retire_chatterbox()  # POST /api/retire: service exits when no request is running
            else:
                sopro_voice_client.stop_sopro()
        result = {
            "status": audit.get("verdict", "UNVERIFIED"),
            "next_step_allowed": audit.get("next_step_allowed", False),
            "voice_output_dir": str(engine.voice_output_dir(folder_path)),
            "manifest": manifest,
            "audit": audit,
        }
    elif stage == 2:
        import documentary_voice_engine as engine
        import documentary_voice_step2 as step2

        out = engine.voice_output_dir(folder_path)
        audit = engine.load_json(out / "voice_audit.json") or {}
        msg = SimpleNamespace(
            data={
                "next_step_allowed": audit.get("next_step_allowed", False),
                "voice_output_dir": str(out),
            }
        )
        plan, review = step2.run_step2(msg, _progress)
        result = {
            "status": review.get("verdict", "UNVERIFIED"),
            "next_step_allowed": review.get("next_step_allowed", False),
            "timeline_path": str(out / step2.SCENE_FILE),
            "review": review,
            "plan": plan,
        }
    elif stage == 3:
        import documentary_voice_engine as engine
        out = engine.voice_output_dir(folder_path)
        timeline = out / "scene_timeline.json"
        effective_sec = int(preview_seconds) if preview_seconds else 0
        mat_out = (out / "03_materials" / f"pilot_{effective_sec}s") if effective_sec > 0 else (out / "03_materials")

        existing_result = engine.load_json(mat_out / "material_result.json") if (mat_out / "material_result.json").is_file() else {}
        _reuse = bool(existing_result and not existing_result.get("final_render_blocked")
                      and not existing_result.get("unresolved")
                      and (mat_out / "material_plan.json").is_file()
                      # Material made under another profile is made again.
                      and _material_profile(mat_out) == profile)
        if _reuse:
            # The plan is reused only when the code that produced it is
            # the code that is running now. Measured on the live run:
            # the material stage was asked to run again after a fix and
            # returned in 0.3 seconds with the old picture, because the
            # reuse did not look at the code at all. A fix that lands
            # after a run has to reach the picture.
            #
            # The signature of the whole package decided, so a comment in
            # runner.py or a fix in an unrelated module ran step 3 again
            # (15-30 minutes a restart on 2026-10-25). runner.stage3_reusable
            # decides by the code step 3 depends on for this film (the
            # catalog's, the plan's, the shot categories it uses) and checks
            # the shots' pictures are on disk; a package that predates it
            # keeps the whole-package rule.
            _why = None
            try:
                from documentary_materials import runner as _runner
                if hasattr(_runner, "stage3_reusable"):
                    _reuse, _why = _runner.stage3_reusable(mat_out, existing_result)
                else:
                    _was = existing_result.get("production_code_signature")
                    _reuse = bool(_was) and _was == _runner._production_code_signature()
            except Exception as exc:
                _reuse, _why = False, "reuse check failed: %s" % exc
            if not _reuse:
                print("3. adim: materyal yeniden uretiliyor (%s): %s" % (_why or "uretim kodu degisti", mat_out), flush=True)
        if _reuse:
            print(f"3. adim: onceden uretilmis ve onaylanmis materyal plani kullaniliyor: {mat_out}", flush=True)
            result = existing_result
            result["status"] = "MATERIALS_READY"
        else:
            _reload_material_modules()
            from documentary_materials.runner import run_step3

            result = run_step3(
                timeline,
                progress=_progress,
                preview_seconds=effective_sec,
                render=False,
                profile=profile,
            )

        result.update({
            "status": "MATERIALS_READY",
            "material_result": str(mat_out / "material_result.json"),
            "output_dir": str(mat_out),
            "material_plan": str(mat_out / "material_plan.json"),
        })
    elif stage == 4:
        import documentary_voice_engine as engine
        out = engine.voice_output_dir(folder_path)
        effective_sec = int(preview_seconds) if preview_seconds else 0
        mat_out = (out / "03_materials" / f"pilot_{effective_sec}s") if effective_sec > 0 else (out / "03_materials")
        if (mat_out / "settings.json").is_file() and _material_profile(mat_out) != profile:
            raise ValueError("Stage 3 material was made under profile %r, not %r; run stage 3 with this profile first"
                             % (_material_profile(mat_out), profile))

        _reuse_final =bool((mat_out / "complete_video.mp4").is_file() and (mat_out / "render_result.json").is_file())
        if _reuse_final:
            # The finished video is reused only when the code that
            # produced it is the code that is running now. The same
            # rule as the material stage: a fix that lands after the
            # run has to reach the film, and the old film was made by
            # older code. render_stage.stage4_reusable decides by the code
            # the render depends on and by the delivered ledger itself (a
            # shot step 3 made again renders the film again); a package
            # that predates it keeps the whole-package rule.
            _why = None
            try:
                from documentary_materials import render_stage as _render_stage
                if hasattr(_render_stage, "stage4_reusable"):
                    _reuse_final, _why = _render_stage.stage4_reusable(mat_out)
                else:
                    from documentary_materials.runner import _production_code_signature
                    _was = (engine.load_json(mat_out / "render_result.json") or {}).get("production_code_signature")
                    _reuse_final = bool(_was) and _was == _production_code_signature()
            except Exception as exc:
                _reuse_final, _why = False, "reuse check failed: %s" % exc
            if not _reuse_final:
                print("4. adim: video yeniden render ediliyor (%s): %s" % (_why or "uretim kodu degisti", mat_out), flush=True)
        if _reuse_final:
            print(f"4. adim: onceden render edilmis nihai video bulundu: {mat_out / 'complete_video.mp4'}", flush=True)
            result = engine.load_json(mat_out / "render_result.json") or {}
        else:
            _reload_material_modules()
            from documentary_materials.render_stage import render_materials
            result = render_materials(mat_out)

        # The delivery ZIP (film, voice, subtitles, cut list, ordered clips)
        # is part of a finished step 4; a reused render reuses its ZIP too.
        from documentary_materials.delivery import package
        result.update({
            "status": result.get("status", "PASS"),
            "video": result.get("video", str(mat_out / "complete_video.mp4")),
            "render_result": str(mat_out / "render_result.json"),
            "delivery_zip": package(out, mat_out),
        })
    else:
        raise ValueError(f"Unknown documentary stage: {stage}")

    result["stage"] = stage
    result["profile"] = profile
    result["folder"] = str(folder_path)
    result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    return _jsonable(result)


class Handler(BaseHTTPRequestHandler):
    server_version = "DocumentaryNativeBridge/1.2"

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)

    def _send(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.rstrip("/")
        if path == "/health":
            self._send(200, {"status": "PASS", "service": "documentary-native-bridge", "port": PORT})
        elif path == "/diag":
            # What is actually running. A code change to this file is
            # supposed to take effect without a restart, and the only
            # way to know that it did is to ask the running process.
            # The stage 3 shortcut used to skip a rebuild when the
            # production code had changed, and the run answered in 0.3
            # seconds with the old picture. That was found by reading
            # the file, not the process, so this reports the state of
            # the process.
            try:
                from documentary_materials.runner import _production_code_signature
                sig = _production_code_signature()
            except Exception as exc:
                sig = "HATA: %s" % exc
            self._send(200, {
                "status": "PASS",
                "bridge_has_code_signature_check": "production_code_signature" in inspect.getsource(run_stage),
                "bridge_uses_narrow_reuse": "stage3_reusable" in inspect.getsource(run_stage),
                "production_code_signature": sig,
                "bridge_source_is_current": not _bridge_source_changed(),
            })
        elif path == "/reload":
            # Reload the pipeline modules in place. The bridge is a long
            # running process, so a code change would otherwise stay
            # invisible until it was restarted - and restarting it is not
            # always possible without stopping work that is in flight.
            try:
                _reload_bridge_itself()
                _reload_material_modules()
                _reload_voice_modules()
                self._send(200, {"status": "PASS", "reloaded": True})
            except Exception as exc:
                self._send(500, {"status": "FAIL", "error": str(exc)})
        else:
            self._send(404, {"status": "NOT_FOUND"})

    def do_POST(self):
        try:
            # A change to this bridge file takes effect on the next
            # request, so the running process never serves code that is
            # already out of date.
            if _bridge_source_changed():
                print("bridge kaynagi degisti, kendini yeniliyor", flush=True)
                _reload_bridge_itself()
                _reload_material_modules()
                _reload_voice_modules()
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            path = self.path.rstrip("/")
            folder_path = body.get("folder_path") or body.get("folder")
            if not folder_path:
                self._send(400, {"status": "FAIL", "error": "Missing folder_path in request body"})
                return

            dry_run = bool(body.get("dry_run", False))
            preview_seconds = int(body.get("preview_seconds", 0) or 0)

            if path in ("/stage1/scan", "/stage/1.1"):
                result = run_stage_1_1(folder_path, dry_run)
            elif path in ("/stage1/prepare", "/stage/1.2"):
                result = run_stage_1_2(folder_path, dry_run)
            elif path in ("/stage1/synthesize", "/stage/1.3"):
                result = run_stage_1_3(folder_path, dry_run)
            elif path in ("/stage1/audit", "/stage/1.4"):
                result = run_stage_1_4(folder_path, dry_run)
            elif path == "/run":
                stage_val = str(body.get("stage", "1")).strip().lower()
                if stage_val in ("1.1", "scan"):
                    result = run_stage_1_1(folder_path, dry_run)
                elif stage_val in ("1.2", "prepare"):
                    result = run_stage_1_2(folder_path, dry_run)
                elif stage_val in ("1.3", "synthesize"):
                    result = run_stage_1_3(folder_path, dry_run)
                elif stage_val in ("1.4", "audit"):
                    result = run_stage_1_4(folder_path, dry_run)
                else:
                    stage_num = int(float(stage_val))
                    # Optional; a body without it keeps the film's stored
                    # profile, and a new film starts as "default".
                    profile = body.get("profile")
                    if profile is not None:
                        from documentary_materials.profiles import PROFILES
                        if str(profile).strip().lower() not in PROFILES:
                            self._send(400, {"status": "FAIL", "error": "Unknown profile %r; known: %s"
                                             % (profile, ", ".join(sorted(PROFILES)))})
                            return
                    result = run_stage(stage_num, folder_path, dry_run, preview_seconds, profile)
            else:
                self._send(404, {"status": "NOT_FOUND", "path": path})
                return

            self._send(200, result)
        except Exception as exc:
            traceback.print_exc()
            self._send(500, {"status": "FAIL", "error_type": type(exc).__name__, "error": str(exc)})


if __name__ == "__main__":
    assert PORT > 0
    print(f"documentary-native-bridge listening on {HOST}:{PORT}", flush=True)
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    # The server is kept as a global so a reload can push a new request
    # handler into it. Without this the running server kept the handler
    # class it was built with, and every change to this file stayed
    # invisible until the process was restarted.
    globals()["SERVER"] = server
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
