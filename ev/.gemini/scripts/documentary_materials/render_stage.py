"""Step 4: render only from the accepted step-3 material ledger."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .io import load, probe, run, save, sha
from .profiles import video_only
from .runner import (CATEGORIES, MIX_TOLERANCE_PERCENT, _concat, _delivered_with_note,
                    _production_code_signature, _source_uses, _valid_result)
from .reservations import (MAX_USES_PER_ORIGIN, MAX_USES_PER_MATERIAL,
                            MIN_SAME_ORIGIN_GAP_SECONDS, footage as _footage)
from .footage import load as _load_footage_groups


def _talking_head_delivery(rows, plan, assets):
    """The people who speak to the camera in the finished film.

    The rule is the film's rule: a person may speak when the narration
    names that person, and a stranger may not. The measurement is on
    the delivered frames, the same way the burned-in subtitle rule is
    measured, because the source window is longer than the shot and a
    face outside the shot is not in the film.
    """
    from .runner import _talking_head_verdict, _FILM_FACE_AREA, _shot_narration, _source_person_text
    from .editorial_gates import narration_allows
    byid = {a["id"]: a for a in assets}
    shots = {int(s["shot_id"]): s for s in plan["shots"]}
    checks = []
    for row in rows:
        artifact = row.get("artifact") or {}
        if artifact.get("category") != "VIDEO":
            continue
        visual = artifact.get("visual_path")
        if not visual or not Path(visual).is_file():
            continue
        stream = next(s for s in probe(visual)["streams"] if s["codec_type"] == "video")
        duration = float(stream.get("duration") or 0)
        if duration <= 0:
            continue
        checks.append((row, {"path": visual, "start": 0.0, "end": duration, "category": "VIDEO"}))
    if not checks:
        return []
    # The verdict is kept beside the delivered picture, keyed on its hash:
    # step 3 measures it, and step 4 (a module reload later, so the memory
    # cache is gone) reads it instead of scanning every shot again, which
    # took 20-30 minutes a film under load (TOPIC_2, 2026-10-26).
    def verdict(check):
        row, probe_asset = check
        sha = (row.get("artifact") or {}).get("visual_sha256")
        kept = Path(probe_asset["path"]).with_name("talking_head.json")
        try:
            old = json.loads(kept.read_text(encoding="utf-8"))
            if sha and old.get("sha") == sha and old.get("area") == _FILM_FACE_AREA:
                return old["verdict"]
        except Exception:
            pass
        found = _talking_head_verdict(probe_asset, min_area_ratio=_FILM_FACE_AREA, samples=5)
        if sha:
            try:
                kept.write_text(json.dumps({"sha": sha, "area": _FILM_FACE_AREA, "verdict": bool(found)}), encoding="utf-8")
            except Exception:
                pass
        return found

    with ThreadPoolExecutor(max_workers=8) as pool:
        verdicts = list(pool.map(verdict, checks))
    flagged = []
    _banned_th_kw = ("interview", "talking head", "seated man", "seated woman",
                     "anchor in a", "studio anchor", "co-anchors", "anchor",
                     "presenter", "reporter to camera", "speaks to camera",
                     "podium", "commentator", "avatar", "press conference")
    for (row, _probe_asset), verdict in zip(checks, verdicts):
        shot = shots.get(int(row["shot_id"]), {})
        text = _shot_narration(shot)
        artifact = row.get("artifact") or {}
        segments = artifact.get("source_segments") or [artifact]
        
        # Check metadata
        meta_viol = False
        for s in segments:
            cid = s.get("id") or s.get("source_id")
            a_meta = byid.get(cid, {})
            txt = ((a_meta.get("description") or "") + " " +
                   (a_meta.get("source_title") or "") + " " +
                   (a_meta.get("composition") or "") + " " +
                   " ".join(a_meta.get("keywords") or [])).lower()
            if any(kw in txt for kw in _banned_th_kw):
                p = _source_person_text(a_meta)
                if not (p and narration_allows(text, p)):
                    meta_viol = True
                    break
        
        if verdict or meta_viol:
            people = [_source_person_text(byid.get(s.get("id"), {})) for s in segments if s.get("id")]
            people = [p for p in people if p]
            if people and any(narration_allows(text, p) for p in people):
                continue
            flagged.append({"shot_id": row["shot_id"], "source_id": (row.get("artifact") or {}).get("source_id"), "vision": verdict, "meta": meta_viol})
    return flagged


def ledger_violations(rows, plan, assets):
    """Every delivery rule the shot ledger breaks, in the order the render checks them.

    rows are the shot results in film order. Each violation is {rule,
    message, reject, requeue}: reject maps each later shot that breaks
    the rule to the footage origins it must not use again; requeue is
    False for a rule a new pick cannot mend (the medium or the length of
    a shot).
    """
    found = []
    order = {int(s["shot_id"]): i for i, s in enumerate(plan["shots"])}
    by_origin = {}
    shot_origins = {}
    for row in rows:
        uses = _source_uses(row.get("artifact") or {}, assets)
        shot_origins[row["shot_id"]] = {_footage(u["origin"]) for u in uses
                                        if u["origin"] and not str(u["origin"]).startswith("generated_3d:")}
        for use in uses:
            by_origin.setdefault(_footage(use["origin"]), []).append({**use, "shot_id": row["shot_id"]})

    def add(rule, message, reject, requeue=True):
        found.append({"rule": rule, "message": message, "requeue": requeue,
                      "reject": {sid: sorted(origins) for sid, origins in reject.items()}})

    # The two repetition rules are delivery gates, not warnings. A film
    # that holds one picture across two shots in a row, or that prints
    # the same source seven times, does not pass.
    adjacent_repeats = []
    previous_visual = None; previous_shot = None
    for row in rows:
        artifact = row.get("artifact") or {}
        visual = artifact.get("visual_sha256") or artifact.get("sha256")
        if visual and visual == previous_visual:
            adjacent_repeats.append({"shot_id": row["shot_id"], "previous_shot_id": previous_shot})
        previous_visual = visual; previous_shot = row["shot_id"]
    if adjacent_repeats:
        add("adjacent_picture", "Adjacent shots repeat the same picture: " + str(adjacent_repeats[:5]) + "; render blocked",
            {r["shot_id"]: shot_origins.get(r["shot_id"], set()) for r in adjacent_repeats})

    # Hard delivery gate: Adjacent shots must not repeat the same source origin.
    # The sources are the cuts of the shot, counted as footage: a sequence
    # carries one origin per cut, and another upload of the same recording
    # is the same source.
    adjacent_origin_repeats = []
    prev_orig = set(); prev_sid = None
    for row in rows:
        orig = shot_origins[row["shot_id"]]
        sid = row.get("shot_id")
        if orig & prev_orig:
            adjacent_origin_repeats.append({"shot_id": sid, "previous_shot_id": prev_sid, "origin": sorted(orig & prev_orig)})
        prev_orig = orig; prev_sid = sid
    if adjacent_origin_repeats:
        add("adjacent_origin", "Adjacent shots repeat the same origin: %s; render blocked" % str(adjacent_origin_repeats[:5]),
            {r["shot_id"]: set(r["origin"]) for r in adjacent_origin_repeats})

    shots_by_id = {int(s["shot_id"]): s for s in plan.get("shots", [])}

    # Hard delivery gate: every shot is delivered in the medium it was
    # planned in. Fallbacks used to turn VIDEO shots into 3D scenes, and
    # the mix check below only warns, so nothing caught the swap.
    medium_swaps = [
        {"shot_id": r["shot_id"], "planned": shots_by_id.get(int(r["shot_id"]), {}).get("category"),
         "delivered": (r.get("artifact") or {}).get("category")}
        for r in rows
        if (r.get("artifact") or {}).get("category") != shots_by_id.get(int(r["shot_id"]), {}).get("category")
    ]
    if medium_swaps:
        add("medium", "Shots delivered in a different medium than planned: %s; render blocked" % str(medium_swaps[:5]),
            {r["shot_id"]: set() for r in medium_swaps}, requeue=False)

    # Hard delivery gate: a video-only film (wildlife profile) is real
    # footage from the first frame to the last, whatever the plan says.
    if video_only(plan.get("targets")):
        not_video = [r["shot_id"] for r in rows if (r.get("artifact") or {}).get("category") != "VIDEO"]
        if not_video:
            add("video_only", "Video-only film carries non-VIDEO shots %s; render blocked" % str(not_video[:5]),
                {sid: set() for sid in not_video}, requeue=False)

    # Hard delivery gate: Opening 30 seconds must be 100% pure VIDEO
    hook_violations = [
        r["shot_id"] for r in rows
        if float(shots_by_id.get(int(r["shot_id"]), {}).get("timeline_start_sec", 0)) < 30.0
        and (r.get("artifact") or {}).get("category") != "VIDEO"
    ]
    if hook_violations:
        add("hook", "Opening 30s hook violation: shots %s are not VIDEO; render blocked" % str(hook_violations),
            {sid: set() for sid in hook_violations}, requeue=False)

    # Hard delivery gate: a still (a PHOTO, or a CARD built from one) holds
    # at most 6.5 s. A still that runs on over a neighbour line no medium could carry (planning's last merge
    # round, continues_over) may hold up to 10 s, the merge's own ceiling.
    merged_ids = {int(s["shot_id"]) for s in plan["shots"] if s.get("continues_over")}
    photo_duration_violations = [
        r["shot_id"] for r in rows
        if (r.get("artifact") or {}).get("category") in ("PHOTO", "CARD")
        # One frame (0.04 s) of tolerance: shot lengths are whole frames.
        and float((r.get("artifact") or {}).get("duration_sec", 0)) > (10.0 if int(r["shot_id"]) in merged_ids else 6.5) + 0.04
    ]
    if photo_duration_violations:
        add("still_length", "Static photo duration exceeded 6.5s ceiling: shots %s; render blocked" % str(photo_duration_violations[:5]),
            {sid: set() for sid in photo_duration_violations}, requeue=False)
    # A generated animation (ANIM) is not a still: it moves for the whole
    # shot, so the 6.5 s ceiling does not hold. Its ceiling is the longest
    # clip the generator makes (anim.MAX_SECONDS, 10 s).
    anim_duration_violations = [
        r["shot_id"] for r in rows
        if (r.get("artifact") or {}).get("category") == "ANIM"
        and float((r.get("artifact") or {}).get("duration_sec", 0)) > 10.0 + 0.04
    ]
    if anim_duration_violations:
        add("anim_length", "Animation duration exceeded the 10s clip ceiling: shots %s; render blocked" % str(anim_duration_violations[:5]),
            {sid: set() for sid in anim_duration_violations}, requeue=False)
    # A motion graphic (MOTION) has the ceiling of a CARD: 6.5 s, or 10 s
    # when it runs on over a merged neighbour line.
    motion_duration_violations = [
        r["shot_id"] for r in rows
        if (r.get("artifact") or {}).get("category") == "MOTION"
        and float((r.get("artifact") or {}).get("duration_sec", 0)) > (10.0 if int(r["shot_id"]) in merged_ids else 6.5) + 0.04
    ]
    if motion_duration_violations:
        add("motion_length", "Motion graphic duration exceeded 6.5s ceiling: shots %s; render blocked" % str(motion_duration_violations[:5]),
            {sid: set() for sid in motion_duration_violations}, requeue=False)
    # A recording may give three excerpts; a photograph, a 3D scene or
    # any other single material may be used once. The cap depends on
    # what the origin is, not on one number for everything. The uses past
    # the cap, latest shots first, are the ones that go.
    over_cap = {}
    for origin, uses in by_origin.items():
        cap = MAX_USES_PER_ORIGIN if any(u.get("category") == "VIDEO" for u in uses) else MAX_USES_PER_MATERIAL
        if len(uses) > cap:
            for u in sorted(uses, key=lambda u: order.get(int(u["shot_id"]), 0))[cap:]:
                over_cap.setdefault(u["shot_id"], set()).add(origin)
    if over_cap:
        add("source_cap", "A source is used more times in the film than it may be: %s; render blocked"
            % str(sorted({o for os_ in over_cap.values() for o in os_})[:5]), over_cap)
    # The three excerpts of one recording have to be far apart inside
    # it. The selection gate holds this while a shot is produced, but
    # the delivery record is read on the finished film, so the rule is
    # checked again on the film itself. The count gate above does not
    # see it: three excerpts of one video pass the count and still read
    # as a loop when they sit in the same minute.
    gap_violations = []
    gap_reject = {}
    for origin, uses in by_origin.items():
        ranged = sorted((u for u in uses if u.get("category") == "VIDEO"), key=lambda u: u["start"])
        # Two uploads of one recording keep separate timelines, so their
        # gap cannot be measured; reservations.allowed keeps one footage
        # to one upload, and this checks the film did. The upload the
        # film reaches first stays.
        uploads = sorted({u["origin"] for u in ranged})
        if len(uploads) > 1:
            gap_violations.append({"origin": origin, "uploads": uploads})
            first = min(ranged, key=lambda u: order.get(int(u["shot_id"]), 0))["origin"]
            for u in ranged:
                if u["origin"] != first:
                    gap_reject.setdefault(u["shot_id"], set()).add(origin)
            continue
        for a, b in zip(ranged, ranged[1:]):
            gap = b["start"] - a["end"]
            if gap < MIN_SAME_ORIGIN_GAP_SECONDS:
                gap_violations.append({"origin": origin, "gap_sec": round(gap, 3),
                                       "from_sec": round(a["start"], 3), "to_sec": round(b["start"], 3)})
                later = max((a, b), key=lambda u: order.get(int(u["shot_id"]), 0))
                gap_reject.setdefault(later["shot_id"], set()).add(origin)
    if gap_violations:
        add("source_gap", "One recording is cut twice closer than %.0f seconds: %s; render blocked"
            % (MIN_SAME_ORIGIN_GAP_SECONDS, str(gap_violations[:5])), gap_reject)
    return found


# The code a finished render depends on (code_identity.py): this module
# and what it calls, as syntax trees, so a comment never renders again.
_STAGE4_CODE = ("render_stage.py", "runner.py", "reservations.py", "footage.py", "editorial_gates.py",
                "profiles.py", "window_index.py")


def stage4_signature(out):
    """What the film in out was rendered from, for the bridge.

    The code in _STAGE4_CODE and the delivered ledger itself: the plan
    rows, the audio, and each shot's status and picture hashes, so a shot
    step 3 made again renders the film again even when no code changed.
    """
    from . import code_identity
    from .io import digest
    out = Path(out)
    plan = load(out / "material_plan.json")
    ledger = []
    for shot in plan["shots"]:
        path = out / "shots" / f'{shot["shot_id"]:04d}' / "result.json"
        row = load(path) if path.is_file() else {}
        artifact = row.get("artifact") or {}
        ledger.append([shot["shot_id"], row.get("status"), artifact.get("sha256"), artifact.get("visual_sha256")])
    settings = load(out / "settings.json") if (out / "settings.json").is_file() else {}
    audio = settings.get("audio_file")
    return digest({"code": code_identity.modules(*_STAGE4_CODE), "plan": digest(plan["shots"]),
                   "audio": sha(audio) if audio and Path(audio).is_file() else None, "ledger": ledger})


def stage4_reusable(out):
    """(True, why) when the finished film in out can be delivered as it is.

    The film and its report have to be on disk and the report has to name
    the ledger and code that run now (stage4_signature). A report of the
    older whole-package rule counts while that rule still holds, and is
    then recorded under the new one.
    """
    out = Path(out)
    final, report_path = out / "complete_video.mp4", out / "render_result.json"
    if not final.is_file() or not report_path.is_file() or not (out / "material_plan.json").is_file():
        return False, "no finished film"
    report = load(report_path) or {}
    if report.get("final_render_blocked") or not report.get("video_sha256"):
        return False, "the last render did not finish"
    now = stage4_signature(out)
    if report.get("stage4_signature") == now:
        return True, "the film is current"
    if "stage4_signature" in report or report.get("production_code_signature") != _production_code_signature():
        return False, "the code or the ledger the film was rendered from changed"
    save(report_path, {**report, "stage4_signature": now})
    return True, "the film is current"


def render_materials(output):
    started=time.perf_counter()
    out=Path(output).resolve()
    plan=load(out/"material_plan.json")
    settings=load(out/"settings.json")
    assets=load(out/"catalog.json")["assets"]
    # The render may run in a process that did not produce the shots, so
    # the footage groups step 3 measured are read from the run folder.
    _load_footage_groups(out)
    audio=settings["audio_file"]
    unresolved=[]
    rows=[]
    for shot in plan["shots"]:
        result_file=out/"shots"/f'{shot["shot_id"]:04d}'/"result.json"
        if not result_file.is_file():
            unresolved.append({"shot_id":shot["shot_id"],"status":"MISSING_RESULT"})
            continue
        result=load(result_file)
        if result.get("status") not in ("PASS","PASS_WITH_WARNINGS") or not _valid_result(result,shot,assets,audio,need_sources=False):
            unresolved.append({"shot_id":shot["shot_id"],"status":result.get("status","INVALID")})
        rows.append(result)
    if unresolved:
        report={"status":"RENDER_BLOCKED","unresolved":unresolved,"final_render_blocked":True,"elapsed_seconds":round(time.perf_counter()-started,3)}
        save(out/"render_result.json",report)
        (out/"REPORT_RENDER.md").write_text('# Render engellendi\n\n'+'\n'.join(f'- Kesit {r["shot_id"]}: {r["status"]}' for r in unresolved),encoding='utf8')
        raise ValueError(f'{len(unresolved)} kesit render için geçerli değil; MP4 oluşturulmadı')
    # The cap on a source is counted on the base YouTube id, because the
    # chunks of one video are one source, and on the footage group, because
    # the re-uploads of one recording are one source too. The delivery record has to
    # show it that way: the reader has to see which shots carry one
    # video, and how many times that video was cut.
    titles={a["id"]:(a.get("source_title") or a.get("title") or "") for a in assets}
    usage={}
    for row in rows:
        artifact=row.get("artifact") or {}
        for use in _source_uses(artifact,assets):
            entry=usage.setdefault(_footage(use["origin"]),{"origin":_footage(use["origin"]),"uses":0,
                                                  "shots":[],"chunks":[],"title":""})
            entry["uses"]+=1
            entry["shots"].append(row["shot_id"])
            chunk=artifact.get("source_id")
            if chunk and chunk not in entry["chunks"]:
                entry["chunks"].append(chunk)
                entry["title"]=titles.get(chunk,"")
    source_usage=sorted(usage.values(),key=lambda e:(-e["uses"],str(e["origin"])))
    max_uses=max([e["uses"] for e in source_usage] or [0])
    # The ledger rules (repeats, medium, hook, still lengths, the source
    # cap and gap); step 3 runs the same function before it declares the
    # material ready, so it only fails here on a ledger step 3 did not see.
    # Shots step 3 could not mend keep their passed picture and are listed
    # in delivery_waivers.json; their rules do not block the render.
    from .runner import _delivery_waivers
    waived=_delivery_waivers(out)
    violations=[v for v in ledger_violations(rows,plan,assets)
                if any(int(sid) not in waived for sid in v["reject"]) or not v["reject"]]
    if violations:
        raise ValueError(violations[0]["message"])
    # A person who speaks to the camera is evidence only when the
    # narration names that person. This is measured on the delivered
    # picture, because that is what the rule is about.
    talking_heads = [h for h in _talking_head_delivery(rows, plan, assets) if int(h["shot_id"]) not in waived]
    if talking_heads:
        raise ValueError("Talking head / interview footage detected in delivered shots: %s; render blocked"
                         % str(talking_heads[:5]))
    _concat(plan,out)
    final=out/"complete_video.mp4"
    media=probe(final);actual=float(media["format"]["duration"])
    stream=next(s for s in media["streams"] if s["codec_type"]=="video")
    expected_frames=plan["shots"][-1]["frame_end"]
    if int(stream.get("nb_frames",-1))!=expected_frames:raise ValueError('Final kare sayısı onaylı zaman çizelgesiyle eşleşmiyor')
    if abs(float(stream["duration"])-expected_frames/25)>.001:raise ValueError('Final video zaman damgası kayması')
    # The whole-film decode on 2 threads (resources.with_threads) under a
    # busy CPU took over 300 s (TOPIC_4, 2026-10-26).
    run(["ffmpeg","-v","error","-i",str(final),"-f","null","-"],1800)
    if abs(actual-float(settings.get("audio_duration_sec",actual)))>.15:raise ValueError('Final video/ses süresi eşleşmiyor')
    seconds={c:sum(int(next(s for s in probe(r["artifact"]["visual_path"])["streams"] if s["codec_type"]=="video")["nb_frames"])/25 for r in rows if r["artifact"]["category"]==c) for c in CATEGORIES}
    total=sum(seconds.values()); percent={c:100*v/total for c,v in seconds.items()};targets=plan.get("targets",{})
    mix_warning={c:round(percent[c]-targets.get(c,0),3) for c in CATEGORIES if abs(percent[c]-targets.get(c,0))>MIX_TOLERANCE_PERCENT}
    # mix_warning is captured in report, not blocking render
    # A shot can be delivered with a note: the reviewer found the footage
    # technically sound and inside the documentary topic, but not a strong
    # match for its specific narration beat. Those shots are accepted by
    # design, so the delivery record has to name them instead of reporting a
    # clean PASS over them. The filter lives in runner._delivered_with_note
    # so both delivery paths name exactly the same shots.
    accepted_partials=[{"shot_id":r["shot_id"],"review":r["review"]["data"]} for r in rows
                       if _delivered_with_note(r["review"]["data"])]
    report={"status":"PASS_WITH_NOTES" if accepted_partials else "PASS","video":str(final),"video_sha256":sha(final),"audio_sha256":sha(audio),"duration_sec":actual,
            "shot_count":len(rows),"actual_percent":percent,"actual_seconds":seconds,"targets":targets,"mix_warning":mix_warning,
            "accepted_partial_reviews":accepted_partials,
            # How often each source was used, counted on the base
            # YouTube id. The chunks of one video are one source, so
            # this is the ledger the cap is read from: three excerpts
            # for a recording, one for a single material.
            "source_usage":source_usage,
            "max_uses_per_origin":max_uses,
            "max_uses_allowed":MAX_USES_PER_ORIGIN,
            "max_uses_allowed_per_material":MAX_USES_PER_MATERIAL,
            # The signature of the code that rendered this film. The
            # bridge reuses a finished video when it is asked to render
            # again, and it has to reuse it only when the code matches.
            "production_code_signature":_production_code_signature(),
            # The narrow signature the bridge decides by (stage4_reusable).
            "stage4_signature":stage4_signature(out),
            "elapsed_seconds":round(time.perf_counter()-started,3),"render_stage":"step4_only"}
    # The material report keeps the step 3 signature it had: the render
    # does not change the material, and without it the bridge would judge
    # step 3 by the whole-package rule again.
    previous=load(out/"material_result.json") if (out/"material_result.json").is_file() else {}
    save(out/"render_result.json",report)
    save(out/"material_result.json",{**report,"status":report["status"],"final_render_blocked":False,
                                     **({"stage3_signature":previous["stage3_signature"]} if previous.get("stage3_signature") else {})})
    note=''
    if accepted_partials:
        note=('\n\nSunum notlarıyla kabul edilen kesitler: %d. Bu kesitler teknik olarak sağlam ve '
              'belgesel konu içinde olup, anlatımın belirli bir vurgusunu güçlü biçimde desteklemeyen '
              'görüntüler nedeniyle notla teslim edildi. Orijinal PARTIAL/FAIL kararları değiştirilmedi; '
              'ayrıntılar material_result.json içindedir.' % len(accepted_partials))
    (out/"REPORT_RENDER.md").write_text(f'# Render sonucu\n\nDurum: {report["status"]}\n\nVideo: `{final}`\n\nSüre: {actual:.3f} sn\n'+note,encoding='utf8')
    return report
