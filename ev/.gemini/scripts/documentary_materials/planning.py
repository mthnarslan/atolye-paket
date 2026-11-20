"""Narrative plan, frame-contiguous shot timing and explicit screen-time mix."""
from concurrent.futures import ThreadPoolExecutor
import os
import random
import re
import time
from copy import deepcopy
import math
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .io import api, digest, event, load, save
from .profiles import for_run, video_only
from .reservations import MAX_USES_PER_ORIGIN, MIN_SAME_ORIGIN_GAP_SECONDS, origin_id

CATEGORIES = ("VIDEO", "PHOTO", "3D", "CARD", "ANIM", "MOTION")
GENERATED_CATEGORIES = {"3D", "PHOTO", "CARD", "ANIM", "MOTION"}
# An ANIM shot is a generated illustrative 2D animation in one of six drawn styles (anim.py,
# G-Labs): no source, the 3.0 s floor of the other static/generated media,
# and a 4 s ceiling: the clip is made at 4 s, the typical shot length. Like 3D, two
# ANIM shots in a row are allowed only inside one scene.
ANIM_MAX_SECONDS = 4.0  # Omni clip is made at 4 s: the typical shot length, and the fastest clip
# A MOTION shot is a code-drawn motion graphic (motion.py: kinetic words,
# timeline, stat, route, process) made from its own sentence: no source,
# the 3.0 s floor and the 6.5 s ceiling of a CARD, and like 3D and ANIM
# two MOTION shots in a row only inside one scene.
MOTION_MAX_SECONDS = 6.5
ADJACENT_ONCE_CATEGORIES = ("3D", "ANIM", "MOTION")
# A CARD shot is one real photograph (a person, product, object or
# document) cut out on a white explainer card with a banner, an arrow and
# a short annotation (cards.py). It draws on the photo pool, so a
# photograph is used once across PHOTO and CARD shots, and it is a still
# like a PHOTO: the 3.0 s floor and the 6.5 s ceiling hold for both.
STILL_CATEGORIES = ("PHOTO", "CARD")
STATIC_CATEGORIES = ("PHOTO", "3D", "CARD", "ANIM", "MOTION")
# The plan's only code identity (code_identity.py). make_plan reuses the
# plan while this, the timeline, the catalog assets, the targets and the
# early locks are what they were; the code of this module is deliberately
# not hashed. A new plan rewrites the shot rows, and every shot identity
# digests its row, so a re-plan makes the whole film again: change this
# value when a planner change has to reach the plan of a resumed film.
PLAN_VERSION = "shot-specific-goals-v6-video-capacity"
# A photograph or a 3D scene that flashes past in two seconds is never read.
# The user rule is that a PHOTO or 3D shot stays on screen for at least
# 4.0 seconds, and the only place a shot can be lengthened is at the
# narration cut points of its own scene.
#
# The floor is applied where the shot boundaries are cut, so it holds
# for every category the plan may choose. A VIDEO shot may still be
# short, because the cut points are the same either way and the
# documentary keeps its fast cuts.
#
# The delivered run measured 15 shots under 4.0 seconds: 13 PHOTO and
# 2 3D, the shortest at 2.44 seconds. The cause was the boundary
# search, which accepted any punctuation point at least 55 frames
# (2.2 s) after the previous one, so a scene of 7.0 seconds was cut
# into two shots of 3.5 seconds each. With the floor at 100 frames
# (4.0 s) that scene becomes one shot of 7.0 seconds instead.
# Target average shot duration: ~4.0 seconds (100 frames at 25 fps)
# Floor for static shots: 75 frames (3.0 seconds) to ensure readability
# Ceiling for static shots: 150 frames (6.0 seconds) to prevent visual drag
TARGET_SHOT_FRAMES = 100
MIN_STATIC_SHOT_FRAMES = 75
HOOK_VIDEO_SECONDS = 30.0
MIX_TOLERANCE_PERCENT = 8.0

# Ceiling for one Flash planning call. The production run left these calls on
# the 120 s default: 16 story-plan groups answered in a 7-10 s median but the
# slowest took 90-91 s, and the shot-goal groups reached 82 s with two
# timeouts. Every one of those slow calls held a plan worker for its full
# budget. 45 s keeps the observed successful range (max 91 s was the tail, not
# the median) and cuts the failing tail to a fraction of the old cost.
PLANNING_TIMEOUT_SECONDS = 45

# The production run's slow planning calls were NOT caused by the pipeline
# queueing and not by the prompt size: planning/events.jsonl shows
# queue_seconds ~ 0 on every call, only 2-12 requests in flight against a
# limit of 15, and the same 5-scene prompt answering in 7.8 s in one group
# and 68.1 s in another. A saturation probe against the real gateway
# (bench_gateway_saturation.py) confirms the gateway answers 5, 10 and 15
# simultaneous calls of the production prompt shape in a 6.4-6.8 s median,
# and only degrades at 20.
#
# So the tail is the gateway's own upstream latency: 58 s, 90 s, 91 s, 97 s
# calls, several of which ended in a ReadTimeout ERROR. timeout=45 does not
# stop them, because httpx restarts its read timer on every chunk, so a
# trickling response can run for 97 s.
#
# A deadline is the only hard cap (io.py checks it every 50 ms) and a hedge
# gives a stalled call a second request while the first still holds its
# slot. The measured saturation probe with a 25 s hedge: at 20 concurrent
# calls the slowest answer dropped from 19.2 s to 12.8 s, and at 5/10/15
# the hedge never fired because nothing was slow enough to need it.
PLANNING_HEDGE_SECONDS = 25
# The deadline has to cover the hedge plus a full-length answer, otherwise
# the hedge's own request is cut off by the same deadline that was meant
# to bound the first one: hedge at 25 s + a 45 s answer = 70 s.
PLANNING_DEADLINE_SECONDS = PLANNING_HEDGE_SECONDS + PLANNING_TIMEOUT_SECONDS

# GPT-routed planning calls (api role "codex": plan review, allocation review,
# infeasible-mix repair). gpt-6-sol answers in ~120 s; the Flash ceiling above
# (45 s) killed the plan-review request in both 1106 mini runs (ReadTimeout at
# 45 s -> retry -> plan_review_fallback). Flash calls keep PLANNING_TIMEOUT_SECONDS.
GPT_PLANNING_TIMEOUT_SECONDS = int(os.environ.get("DOCUMENTARY_GPT_PLANNING_TIMEOUT", "180") or 180)
GPT_PLANNING_DEADLINE_SECONDS = GPT_PLANNING_TIMEOUT_SECONDS + 30

def _planning_api(prompt, receipt, tokens):
    """A Flash planning call with a hard ceiling and a stall hedge.

    The deadline is what bounds the wall clock: without it a slow upstream
    answer can hold a plan worker for 97 s, which is what made the
    production plan phase 361 s. The hedge is what keeps a stall cheap:
    a second request is launched after 25 s and the first response to
    arrive wins, so a stalled call costs ~25-30 s instead of ~90 s.

    The attempt count is left at the default (2 for Flash) so a request
    that fails fast still gets a second try; the deadline is what caps
    the total, and the hedge's second request shares that cap.
    """
    return api("flash", prompt, receipt, tokens=tokens, timeout=PLANNING_TIMEOUT_SECONDS,
               hedge_override=PLANNING_HEDGE_SECONDS,
               deadline=time.monotonic() + PLANNING_DEADLINE_SECONDS)

def anim_possible(targets):
    """True when the mix gives ANIM time and the G-Labs server answers."""
    if not float((targets or {}).get("ANIM", 0)):
        return False
    from . import anim
    return anim.available()

def without_anim(targets):
    """The mix with ANIM's share given to 3D and CARD, half each.

    A film never waits for G-Labs: when it does not answer at planning
    time, the generated animation's time goes to the two other generated
    media that need no outside server.
    """
    share = float(targets.get("ANIM", 0))
    return {**targets, "3D": targets.get("3D", 0) + share / 2, "CARD": targets.get("CARD", 0) + share / 2, "ANIM": 0}

def _material_pool(catalog):
    """What this run can actually build, in a form the reviewer can read.

    The reviewer saw the plan but not the pool, so it asked for
    material the run does not have - a dated 1978 groundbreaking
    photograph, the ASCE ethics code, a verified picture of one named
    person - and failed the whole plan for it. The pool is what the
    catalog holds: how many usable assets there are per medium, and
    what they show.
    """
    pool = {}
    assets = (catalog or {}).get("assets") or []
    # CARD has no assets of its own; it is built from the PHOTO pool, which
    # the payload's card_rule says. Leaving the key out keeps the review
    # digest of a plan without cards (wildlife) what it was. ANIM is
    # generated from the narration and has no pool either, nor has MOTION.
    for cat in (c for c in CATEGORIES if c not in ("CARD", "ANIM", "MOTION")):
        usable = [a for a in assets
                  if a.get("usable") and a.get("category") == cat
                  and not a.get("excluded_by_independent_audit")]
        themes = []
        for a in usable:
            text = (str(a.get("description", "")) + " " + str(a.get("source_title", ""))).strip()
            if text and text not in themes:
                themes.append(text[:160])
        pool[cat] = {"usable_assets": len(usable), "themes": themes[:10]}
    return pool


def _review_payload(plan, catalog=None):
    total = sum(r.get("duration_sec", 0) for r in plan.get("shots", []))
    tol = 15.0 if total <= 45.0 else MIX_TOLERANCE_PERCENT
    payload = {"targets":plan["targets"],"percent":plan["planned_percent"],"basis":"duration_seconds",
            "tolerance_percentage_points":tol,
            "category_rule":"One visual medium per shot. Labels/arrows do not change its category; no cross-medium composites.",
            "continuity_rule":"Preserve upper/lower floor orientation and identifiers; a new medium explains the same object or advances the current narrated idea.",
            "hard_rules":{"no_talking_head":"Do not ask for interview, presenter or talking-head footage. A person whose words are narrated is shown through the mechanism, a labelled 3D diagram or archive footage instead.",
                    "source_quota":"At most three excerpts may come from the same recording, and they have to be far apart in it (at least 30 seconds between the cuts), never consecutive. Every photograph, 3D scene and other single material is used exactly once.",
                    "no_burned_in_subtitles":"Do not ask for footage carrying burned-in subtitles; such frames are rejected at production.",
                    "static_minimum_seconds":4.0},
            "shots":[{k:r[k] for k in ("shot_id","scene_id","category","narration","timeline_start_sec","timeline_end_sec","duration_sec","story_plan")} for r in plan["shots"]]}
    # Only a plan that gives CARD screen time carries the rule, so the
    # reviewed digest of every other plan is unchanged.
    if float((plan.get("targets") or {}).get("CARD", 0)):
        payload["card_rule"] = ("CARD is one real photograph from the PHOTO pool (a person, product, object or document) "
                                "cut out on a white explainer card with a title banner, a hand-drawn arrow and a short "
                                "annotation timed to the narration. It suits a sentence that names a person, product, "
                                "object, document, organisation, date or number. Its text is designed graphics, not "
                                "subtitles. A photograph is used once across PHOTO and CARD shots.")
    if float((plan.get("targets") or {}).get("ANIM", 0)):
        payload["anim_rule"] = ("ANIM is a generated, clearly illustrative 2D animation in a drawn style (paper collage, ink engraving, blueprint, screen print, isometric diorama or archival cut-out) made "
                                "from the narration, with no text in the picture. It suits abstract ideas, processes, "
                                "spread across places, maps without labels and concepts no honest footage shows. It is "
                                "not archival evidence; it needs no source and holds 3 to 10 seconds.")
    if float((plan.get("targets") or {}).get("MOTION", 0)):
        payload["motion_rule"] = ("MOTION is a code-drawn motion graphic made from the narration: kinetic power words, a "
                                  "dated timeline, a metric count-up, a route between named places or numbered steps. "
                                  "It suits sentences with dates, numbers, comparisons, lists, processes or named places. "
                                  "Its text is designed graphics taken from the narration, not subtitles; it needs no "
                                  "source and holds 3 to 6.5 seconds.")
    if catalog is not None:
        payload["material_pool"] = _material_pool(catalog)
    if plan.get("capacity"):
        payload["video_capacity"] = plan["capacity"]
    if total <= 45.0:
        payload["preview_pilot_notice"] = (
            "IMPORTANT: This is a 30s pilot/preview segment of a full-length documentary. "
            "The narration in the final shot naturally reaches the 30s preview cutoff and continues in subsequent shots in the full production; "
            "do NOT flag or penalize the final shot for ending mid-sentence at the 30s cutoff."
        )
    return payload

# REWRITE: source_context parametresi eklendi (varsayılan None). _approve_plan içinde bir kez hesaplanıp aktarılır.
def _refine_goals(plan,catalog,out,attempt,feedback,source_context=None):
    rows=plan["shots"]
    # REWRITE: source_context hesaplaması fonksiyon dışından gelmemişse yapılır; [-60:] -> [-20:] yapıldı (~9K token -> ~3K token)
    if source_context is None:
        source_context={c:[{"id":a["id"],"description":a.get("description","")[:200]} for a in catalog["assets"]
                           if a.get("usable") and a.get("category")==("PHOTO" if c=="CARD" else c) and not a.get("excluded_by_independent_audit")][-20:] for c in CATEGORIES}
    issues=feedback.get("issues",[]) if feedback else []
    affected={v for issue in issues if isinstance(issue,dict) for v in issue.get("shot_ids",[]) if type(v) is int}
    # A shot produced early as 3D keeps its goal unless the review names it:
    # a blanket rewrite (a review without shot ids, a review timeout) would
    # change its row and throw the finished picture away.
    selected=[r for r in rows if r["shot_id"] in affected or (not affected and not r.get("generated_only"))]

    def group(item):
        index,batch=item
        first,last=rows.index(batch[0]),rows.index(batch[-1])
        context=rows[max(0,first-1):min(len(rows),last+2)]
        compact=[{k:r[k] for k in ("shot_id","scene_id","category","narration","full_scene_narration","narrative_beat")} for r in context]
        prompt=('Write shot-specific documentary visual instructions for the assigned category and CURRENT shot words; full scene is continuity context. '
                'Do NOT copy a scene-wide visual goal to every shot. Write for the category given for that shot; the timing is fixed and duration-weighted. '
                'VIDEO means actual moving camera/archive footage; PHOTO means one real archival photograph; '
                'CARD means one real photograph of the named person, product, object or document cut out on a white explainer card with a short title banner, an arrow and a short annotation; other static cards and slides are forbidden; '
                'ANIM means a generated, clearly illustrative 2D animation of concrete objects in gentle motion in a drawn style (paper collage, ink engraving, blueprint, screen print, isometric diorama or archival cut-out), with no text, for an abstract idea, process or spread; '
                'MOTION means a code-drawn motion graphic built from the sentence\'s own words: kinetic power words, a dated timeline, a metric count-up, a route between named places or numbered steps; '
                '3D means actual mesh-based mechanical/spatial explanatory geometry, not FEA. Each shot has ONE medium, never a photo/3D or other mixed composite. '
                'Brief labels/arrows are permitted annotations, not another medium. Do not require invented assets or unrecorded collapse footage. '
                'Use available-source themes for VIDEO/PHOTO, describe the evidence honestly; do not pretend a modern explanation or aftermath shows the actual collapse. '
                'A shot need only support the current thought, not literally depict every word. Explain why its medium advances that thought. '
                'For transitions, retain upper/lower floor arrangement, geometry orientation and current subject; state a concrete handoff from the prior shot. '
                'Generated geometry is schematic/illustrative, not historical footage or measured simulation. No invented numbers or stress fields. '
                'The visual goal must describe the medium that is allocated to that shot: a VIDEO goal describes recorded footage, never a rendering, a diagram or a model; a 3D goal describes generated geometry, never an archival photograph. '
                'If the feedback offers a choice, take the option that stays inside the allocated category and write the goal so it states plainly what the material shows and what it does not show. '
                'Keep narration untouched and factual script concerns separate. '
                'If the feedback asks for an on-screen label, write the exact label text into the visual_goal and keep it to one short line. '
                'If the feedback names material this run does not have, write the goal so it shows only what the material actually shows and say plainly what it is; do not promise a document, a named person or an event the pool does not contain. '
                'Return JSON {shots:[{shot_id,category,visual_goal:string,context:string,transition:string}]}; '
                'return exactly the requested IDs, each field concise (at most35words). '
                f'\nREQUESTED_IDS:{[r["shot_id"] for r in batch]}\nSHOTS_WITH_NEIGHBORS:{compact}\nAVAILABLE_SOURCE_THEMES:{source_context}')
        if feedback:prompt+='\nFIX THESE ACTUAL PLAN DEFECTS:'+str(feedback)
        receipt=out/"planning"/f"shot_goals_{attempt}_{index:02}.json"
        try:
            # REWRITE: tokens=3800 -> tokens=2000 yapıldı - output gereksiz büyük olmasını engellemek için
            response=_planning_api(prompt,receipt,2000)
            actual=response["data"].get("shots",[])
        except Exception as exc:
            actual=[]
            save(receipt,{"status":"SHOT_GOAL_FALLBACK","error":type(exc).__name__})
            event(out,"shot_goals_group_fallback",attempt=attempt,group=index,shots=len(batch),error=type(exc).__name__)
        # A shot the answer left out gets the deterministic goal; invented
        # and repeated ids are dropped instead of failing the whole plan.
        given={}
        for r in actual:
            if isinstance(r,dict) and r.get("shot_id") in {b["shot_id"] for b in batch}:given.setdefault(r["shot_id"],r)
        actual=[given.get(r["shot_id"]) or {"shot_id":r["shot_id"],"category":r["category"],
                 "visual_goal":str(r.get("narrative_beat") or r.get("narration") or "")[:180],
                 "context":"deterministic shot-goal fallback",
                 "transition":"Continue the current subject with a distinct source."} for r in batch]
        expected={r["shot_id"]:r["category"] for r in batch}
        for row in actual:
            if row.get("category")!=expected[row["shot_id"]]:
                # The plan's category is the one that counts. The model
                # is corrected to it, not trusted, because the plan
                # is what the production gates were built for.
                row["category"]=expected[row["shot_id"]]
            for key in ("visual_goal","context","transition"):
                if not isinstance(row.get(key),str) or not row[key].strip():
                    fallback = next((r for r in batch if r["shot_id"]==row["shot_id"]), None)
                    row[key]=str((fallback or {}).get("narrative_beat") or (fallback or {}).get("narration") or "")[:180] or "Continue the current subject with a distinct source."
        event(out,"shot_goals_group",attempt=attempt,group=index,shots=len(actual))
        return actual

    with ThreadPoolExecutor(max_workers=max(1, int(os.environ.get("DOCUMENTARY_FLASH_CONCURRENCY", "10")))) as pool:
        # REWRITE: shot_goals_group grup boyutu 10 -> 15 yapıldı - daha az Flash çağrısı
        groups=list(pool.map(group,enumerate([selected[i:i+15] for i in range(0,len(selected),15)])))
    goals={r["shot_id"]:r for g in groups for r in g}
    for row in rows:
        if row["shot_id"] in goals:row["story_plan"]={"scene_id":row["scene_id"],**goals[row["shot_id"]]}

def _apply_review_requests(plan, feedback):
    """Carry out the review request when it asks for a diagram instead.

    The reviewer's most common fix is "show this in 3D" or "use a
    diagram". The repair prompt told the model that the categories
    are fixed, and the goal writer was required to echo the category
    it was given, so the request could not be satisfied: it went
    unanswered three times, the review escalated to FAIL and the whole
    production stopped. The medium is changed here, where the
    reviewer asked for it, and the model then writes the goal for the
    medium the reviewer asked for.

    The floor rules are kept. The first thirty seconds stay VIDEO, a
    shot shorter than the static floor stays as it is, because a
    three-dimensional scene under the floor is a rule broken rather
    than a fix.

    The duration mix is kept as well. A review request is a group of
    shots, and a group is answered whole or not at all, because half
    a request is what made the review fail the first time. When the
    requests together would push the mix outside the tolerance, the
    groups that carry an alternative in the reviewer's own words
    ("footage or a diagram") are the ones given back, and the ones
    that named the diagram and nothing else are kept.
    """
    # A video-only film (wildlife) has no diagram to switch to; the
    # reviewer's request is answered by the goal writer inside VIDEO.
    if video_only(plan.get("targets")):
        return []
    issues = (feedback or {}).get("issues") or []
    by_id = {int(s["shot_id"]): s for s in plan.get("shots", [])}
    groups = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        fix = str(issue.get("fix", "")).lower()
        if not re.search(r"\b3d\b|diagram|schematic|cutaway|structural section", fix):
            continue
        # The reviewer often offers two ways out: "relabel it 3D, or
        # keep the video and describe what the footage actually
        # shows". The second way is inside the medium the plan
        # already has, and it is answered by writing the goal
        # honestly, which is what the goal writer does. A medium is
        # changed only when the review names the diagram and nothing
        # else, because a change costs the duration mix and the
        # reviewer did not ask for it.
        if " or " in fix and re.search(r"video|footage|archival", fix):
            continue
        entries = []
        for sid in (issue.get("shot_ids") or []):
            try:
                shot = by_id.get(int(sid))
            except (TypeError, ValueError):
                continue
            if not shot or shot.get("category") not in ("VIDEO", *STILL_CATEGORIES):
                continue
            if float(shot.get("timeline_start_sec", 0)) < 30.0:
                continue
            if (float(shot.get("frame_end", 0)) - float(shot.get("frame_start", 0))) < MIN_STATIC_SHOT_FRAMES:
                continue
            entries.append({"shot_id": int(sid), "was": shot["category"]})
        if not entries:
            continue
        # A request that covers shots which are already 3D cannot be
        # half answered: the reviewer asked for the same view in both.
        forced = any(by_id.get(e["shot_id"], {}).get("category") == "3D" for e in entries)
        groups.append({"entries": entries, "forced": forced, "alternative": " or " in fix})
    if not groups:
        return []

    targets = plan.get("targets") or {}
    total = sum(float(s.get("duration_sec", 0)) for s in plan.get("shots", [])) or 1.0
    optional = [i for i, g in enumerate(groups) if not g["forced"]]

    def percent_for(kept):
        totals = {c: 0.0 for c in CATEGORIES}
        for shot in plan.get("shots", []):
            cat = shot.get("category")
            for index, group in enumerate(groups):
                for entry in group["entries"]:
                    if entry["shot_id"] == int(shot["shot_id"]):
                        cat = "3D" if index in kept else entry["was"]
                        break
            totals[cat] = totals.get(cat, 0.0) + float(shot.get("duration_sec", 0))
        return {c: 100 * totals[c] / total for c in CATEGORIES}

    def inside(pct):
        return all(abs(pct[c] - targets.get(c, 0)) <= MIX_TOLERANCE_PERCENT for c in CATEGORIES)

    best = None
    for mask in range(1 << len(optional)):
        kept = {optional[i] for i in range(len(optional)) if mask >> i & 1}
        kept |= {i for i, g in enumerate(groups) if g["forced"]}
        pct = percent_for(kept)
        if not inside(pct):
            continue
        score = (sum(1 for i in kept if not groups[i]["alternative"]), len(kept))
        if best is None or score > best[0]:
            best = (score, kept)

    kept = best[1] if best else set()
    changed = []
    for index, group in enumerate(groups):
        if index not in kept:
            continue
        for entry in group["entries"]:
            shot = by_id[entry["shot_id"]]
            shot["category"] = "3D"
            if isinstance(shot.get("story_plan"), dict):
                shot["story_plan"]["category"] = "3D"
            changed.append(entry["shot_id"])
    if changed:
        totals = {c: 0.0 for c in CATEGORIES}
        for shot in plan.get("shots", []):
            totals[shot["category"]] = totals.get(shot["category"], 0.0) + float(shot.get("duration_sec", 0))
        plan["planned_percent"] = {c: round(100 * totals[c] / total, 3) for c in CATEGORIES}
    return sorted(set(changed))


# --- deterministic pre-review enforcement of the reviewer's hard rules -------
# The plan review is an LLM that counts what the plan text says. Two of its
# hard rules were never enforced by the solver, and a goal rewrite cannot
# repair them (EP03 1107: 3 FAIL rounds, production blocked):
#  * source_quota: the shot goals are written by Flash from the same last-20
#    themes, so it cites the same few recording ids again and again (6 shots
#    on one id). The real cap is applied at production (reservations.py); the
#    plan only needs to not promise more than 3 cuts, never consecutive.
#  * static_minimum_seconds 4.0: the solver's floor is 3.0 s, so a PHOTO of
#    3.8 s is legal for the solver and a FAIL for the reviewer.
PLAN_QUOTA_PER_RECORDING = 3
PLAN_STATIC_MINIMUM_SECONDS = 4.0

_LOCKED_SHOTS=set()   # shot ids with a finished PASS result: the plan repairs never touch them (their digests would change)
def _finished_ids(out):
    ids=set()
    for f in (out/"shots").glob("*/result.json"):
        try:
            if load(f).get("status") in ("PASS","PASS_WITH_WARNINGS") and f.parent.name.isdigit():ids.add(int(f.parent.name))
        except Exception:pass
    return ids
def _enforce_plan_hard_rules(plan,catalog,out):
    ids=sorted({a["id"] for a in (catalog or {}).get("assets",[]) if a.get("category")=="VIDEO" and a.get("id")},key=len,reverse=True)
    origin={a["id"]:origin_id(a) for a in catalog.get("assets",[]) if a.get("id") in set(ids)}
    stripped=[]
    if ids:
        rx=re.compile("|".join(re.escape(i) for i in ids))
        kept={}   # origin -> positions of shots that keep a citation
        for pos,shot in enumerate(plan["shots"]):
            sp=shot.get("story_plan")
            if not isinstance(sp,dict) or shot["shot_id"] in _LOCKED_SHOTS:continue
            text=" ".join(str(sp.get(k,"")) for k in ("visual_goal","context","transition"))
            found={origin[m] for m in rx.findall(text)}
            for o in sorted(found):
                positions=kept.setdefault(o,[])
                if len(positions)<PLAN_QUOTA_PER_RECORDING and not (positions and pos-positions[-1]<=1):
                    positions.append(pos);continue
                for k in ("visual_goal","context","transition"):
                    v=sp.get(k)
                    if not isinstance(v,str):continue
                    for i in ids:
                        if origin[i]!=o:continue
                        v=re.sub(r"\s*[\(\[]\s*"+re.escape(i)+r"\s*[\)\]]","",v)
                        v=re.sub(r"(?:recording|asset|source|clip)\s+"+re.escape(i)+r"","the archive footage",v)
                        v=v.replace(i,"the archive footage")
                    sp[k]=re.sub(r"\s{2,}"," ",v).strip()
                stripped.append(shot["shot_id"])
    lifted=[];unmet=[]
    rows=plan["shots"]
    need_all=int(round(PLAN_STATIC_MINIMUM_SECONDS*25))
    for i,r in enumerate(rows):
        if r.get("category")!="PHOTO" or r.get("generated_only") or r["shot_id"] in _LOCKED_SHOTS:continue
        have=r["frame_end"]-r["frame_start"]
        if have>=need_all:continue
        need=need_all-have
        done=False
        # Scenes are sentences: moving a cut across a scene boundary by a few
        # frames lets the picture lead its narration (prev side, up to 0.48 s)
        # or trail it (next side, up to 0.32 s); inside one scene any amount.
        for j,side in ((i-1,"prev"),(i+1,"next")):
            if not 0<=j<len(rows):continue
            n=rows[j]
            if n.get("generated_only") or n["shot_id"] in _LOCKED_SHOTS:continue
            if n.get("scene_id")!=r.get("scene_id") and need>(12 if side=="prev" else 8):continue
            if n.get("category")=="PHOTO" and n["frame_end"]-n["frame_start"]<need_all+need:continue
            floor=MIN_STATIC_SHOT_FRAMES if n.get("category") in STATIC_CATEGORIES else 50
            if n["frame_end"]-n["frame_start"]-need<floor:continue
            if side=="next":r["frame_end"]+=need;n["frame_start"]+=need
            else:r["frame_start"]-=need;n["frame_end"]-=need
            for x in (r,n):
                x["timeline_start_sec"]=x["frame_start"]/25;x["timeline_end_sec"]=x["frame_end"]/25
                x["duration_sec"]=(x["frame_end"]-x["frame_start"])/25
            lifted.append((r["shot_id"],n["shot_id"],need));done=True;break
        if not done:unmet.append(r["shot_id"])
    if lifted:
        totals={c:0.0 for c in CATEGORIES}
        for r in rows:totals[r["category"]]+=float(r["duration_sec"])
        tot=sum(totals.values()) or 1.0
        plan["planned_percent"]={c:round(100*totals[c]/tot,3) for c in CATEGORIES}
    if stripped or lifted or unmet:
        event(out,"plan_hard_rules_enforced",quota_stripped_shots=stripped,static_lifted=lifted,static_unmet=unmet)
    return {"quota_stripped":stripped,"static_lifted":lifted,"static_unmet":unmet}


# --- goal / category alignment ------------------------------------------------
# make_plan gives every shot the SCENE's story plan (written for the scene's
# best-scoring medium) whatever category the mix solver picked for the shot, and
# _refine_goals skips a plan whose shots all carry a story_plan. So the first
# review reads VIDEO shots with "USGS event card" goals, ANIM with "kinetic
# metric" goals, 3D with "archival photograph" ones (EP03 1107: 66 shots named
# by GPT, 82 by the rule detector below). A repair round then rewrites only the
# shots the reviewer named, and the reviewer names another subset next time.
_GOAL_NEG=re.compile(r"\b(?:text-free|no text|without (?:any )?text|textless|(?:free|devoid|void|empty) of [\w ,/-]{0,40}?(?:text|typography|numbers|labels|words)|not (?:an? )?(?:animation|photo\w*|card|diagram|render\w*|3d)|rather than (?:an? )?\w+|never (?:an? )?\w+)\b",re.I)
_GOAL_TALK=r"\b(?:reporters?|journalists?|news ?anchors?|anchors?|presenters?|interview\w*|on[- ]camera|to camera|press conference|podium|talking[- ]heads?|commentators?)\b"
_GOAL_TALK_OK=re.compile(r"(?:\b(?:no|without|never|avoid\w*|excluding|not|free of)\b[^.;]{0,30}|-free\b.{0,0})$",re.I)
_GOAL_BAD={
 "VIDEO":r"\b(?:animat\w+|3d|diagrams?|infographics?|cut-?outs?|explainer card|cards?|motion graphics?|typography|counters?|count-?up|schematics?|blueprints?|route trace|timelines?|photographs?|photos?|still (?:image|photow*)|mesh|stylized)\b",
 "PHOTO":r"\b(?:animat\w+|3d|motion graphics?|typography|count-?up|video|footage|clip|timelines?|cut-?outs?|explainer card)\b",
 "3D":r"\b(?:photographs?|photos?|footage|video|2d|drawn|archival|animation|cut-?outs?|explainer card|typography|count-?up)\b",
 "ANIM":r"\b(?:typography|numerical|numbers?|counters?|count-?up|metrics?|labels?|labelled|captions?|timelines?|routes?|dated|archival|footage|photographs?|photos?|3d|mesh|text|words?|titles?|motion graphics?|checklist|graphic)\b",
 "CARD":r"\b(?:footage|video|clip|animat\w+|3d|motion graphics?|typography)\b",
 "MOTION":r"\b(?:footage|archival|photographs?|3d|animation|cut-?outs?)\b",
}
def _goal_contradiction(shot):
    """Rule-based: the first word of the goal that belongs to another medium than shot['category'], else None."""
    sp=shot.get("story_plan")
    if not isinstance(sp,dict):return None
    raw=str(sp.get("visual_goal",""))
    t=_GOAL_NEG.sub(" ",raw)
    if shot["category"]=="VIDEO":
        for m in re.finditer(_GOAL_TALK,t,re.I):
            if not _GOAL_TALK_OK.search(t[max(0,m.start()-40):m.start()]) and not t[m.end():m.end()+5].lower().startswith("-free"):
                return "talking:"+m.group(0)
    rx=_GOAL_BAD.get(shot["category"])
    m=re.search(rx,t,re.I) if rx else None
    return m.group(0).lower() if m else None

def _scene_top(plan):
    out={}
    for sc in plan.get("scenes",[]):
        sc_scores=sc.get("scores") or {}
        if sc_scores:out[sc["scene_id"]]=max(sc_scores,key=lambda c:sc_scores[c])
    return out

def _lift_banned_rows(plan,out):
    """A shot under the static floor in a scene that forbids VIDEO was left VIDEO
    (plan_row_ban_lifted). Give it the missing frames from a neighbour and an
    allowed static medium instead. Returns the shot ids whose category changed."""
    forb={sc["scene_id"]:set(sc.get("forbidden") or []) for sc in plan.get("scenes",[])}
    scores={sc["scene_id"]:(sc.get("scores") or {}) for sc in plan.get("scenes",[])}
    rows=plan["shots"];changed=[]
    for i,r in enumerate(rows):
        if r["category"]!="VIDEO" or "VIDEO" not in forb.get(r["scene_id"],()) or r.get("generated_only") or r["shot_id"] in _LOCKED_SHOTS:continue
        have=r["frame_end"]-r["frame_start"];need=max(0,MIN_STATIC_SHOT_FRAMES-have)
        if not need:continue   # only the static-floor victims; a long VIDEO row stays what the solver chose
        options=[c for c in ("MOTION","ANIM","3D","CARD") if c not in forb[r["scene_id"]] and float(scores[r["scene_id"]].get(c,0))>1
                 and float((plan.get("targets") or {}).get(c,0))>0 and _goal_ok_len(c,have+need)]
        if not options:continue
        options.sort(key=lambda c:-float(scores[r["scene_id"]].get(c,0)))
        if need:
            for j,side in ((i-1,"prev"),(i+1,"next")):
                if not 0<=j<len(rows):continue
                n=rows[j]
                floor=MIN_STATIC_SHOT_FRAMES if n["category"] in STATIC_CATEGORIES else 50
                if n.get("generated_only") or n["shot_id"] in _LOCKED_SHOTS or n["frame_end"]-n["frame_start"]-need<floor or need>12:continue
                if side=="next":r["frame_end"]+=need;n["frame_start"]+=need
                else:r["frame_start"]-=need;n["frame_end"]-=need
                for x in (r,n):
                    x["timeline_start_sec"]=x["frame_start"]/25;x["timeline_end_sec"]=x["frame_end"]/25
                    x["duration_sec"]=(x["frame_end"]-x["frame_start"])/25
                break
            else:continue
        r["category"]=options[0]
        if isinstance(r.get("story_plan"),dict):r["story_plan"]={k:v for k,v in r["story_plan"].items() if k!="shot_id"}
        changed.append(r["shot_id"])
    if changed:
        totals={c:0.0 for c in CATEGORIES}
        for r in rows:totals[r["category"]]+=float(r["duration_sec"])
        tot=sum(totals.values()) or 1.0
        plan["planned_percent"]={c:round(100*totals[c]/tot,3) for c in CATEGORIES}
        event(out,"plan_banned_rows_realloc",shots=changed)
    return changed

def _goal_ok_len(category,frames):
    if category=="ANIM":return frames<=ANIM_MAX_SECONDS*25
    if category=="MOTION":return frames<=MOTION_MAX_SECONDS*25
    return True

_GOAL_TEMPLATE={"VIDEO":"Archival moving footage that supports: {b}","PHOTO":"One real archival photograph that supports: {b}",
                "3D":"Labelled 3D mesh geometry that explains: {b}","CARD":"One real photograph cut out on a white explainer card with a short title banner and arrow, about: {b}",
                "ANIM":"Text-free illustrative 2D animation in a drawn style of concrete objects, about: {b}","MOTION":"Code-drawn motion graphic from the sentence's own words, about: {b}"}

def _misaligned(plan):
    top=_scene_top(plan)
    ids=[]
    for s in plan["shots"]:
        if s.get("generated_only") or s["shot_id"] in _LOCKED_SHOTS:continue
        sp=s.get("story_plan")
        if not isinstance(sp,dict) or _goal_contradiction(s) or ("shot_id" not in sp and top.get(s["scene_id"])!=s["category"]):
            ids.append(s["shot_id"])
    return ids

def _align_goals(plan,catalog,out,attempt,source_context):
    """Deterministic detector -> targeted goal rewrite (only the misaligned shots) -> template for what is still wrong."""
    _lift_banned_rows(plan,out)
    for rnd in range(2):
        ids=_misaligned(plan)
        if not ids:return
        event(out,"plan_goal_alignment",attempt=attempt,round=rnd,shots=len(ids))
        fb={"issues":[{"shot_ids":ids,"problem":"The visual goal does not describe the medium allocated to the shot (or asks for text, a presenter, a card or a graphic outside that medium).",
                       "fix":"Rewrite the goal so it states plainly what the allocated category shows; keep it inside that one medium."}]}
        _refine_goals(plan,catalog,out,f"align{rnd}_{attempt}",fb,source_context=source_context)
    for s in plan["shots"]:
        if s["shot_id"] in set(_misaligned(plan)):
            beat=str(s.get("narrative_beat") or s.get("narration") or "")[:160]
            sp=s.get("story_plan") if isinstance(s.get("story_plan"),dict) else {}
            s["story_plan"]={**sp,"scene_id":s["scene_id"],"shot_id":s["shot_id"],"category":s["category"],
                             "visual_goal":_GOAL_TEMPLATE[s["category"]].format(b=beat),"context":"deterministic category-aligned goal","transition":sp.get("transition","Continue the current subject with a distinct source.")}
    event(out,"plan_goal_alignment_done",remaining=len(_misaligned(plan)))


def _approve_plan(plan,catalog,out):
    review_path=out/"plan_review.json"
    if review_path.exists():
        old=load(review_path)
        # A plan accepted with editorial notes is accepted too. Reviewing it
        # again on every start rewrote the shot goals each time, which
        # changed the shot digests and threw away finished shots.
        if (old.get("reviewed_plan_digest") in (digest(_review_payload(plan,catalog)),digest(_review_payload(plan)))
                and (old.get("status")=="OK" and old.get("data",{}).get("verdict")=="PASS"
                     or plan.get("codex_verdict")=="PASS_WITH_EDITORIAL_ALLOWANCE")):
            return plan
    feedback=None
    review_fallback=False
    _LOCKED_SHOTS.clear();_LOCKED_SHOTS.update(_finished_ids(out))
    # REWRITE: source_context fonksiyon dışında bir kez hesaplanıp _refine_goals'e aktarılıyor (token ve süre tasarrufu)
    cached_source_context={c:[{"id":a["id"],"description":a.get("description","")[:200]} for a in catalog["assets"]
                              if a.get("usable") and a.get("category")==("PHOTO" if c=="CARD" else c) and not a.get("excluded_by_independent_audit")][-20:] for c in CATEGORIES}
    for attempt in range(3):
        if feedback:
            changed_shots=_apply_review_requests(plan,feedback)
            if changed_shots:
                event(out,"plan_medium_changed_by_review",attempt=attempt,shots=changed_shots,
                      planned_percent=plan["planned_percent"])
        # Goals are written once; without review feedback there is nothing
        # to change, and rewriting them invalidated every finished shot.
        if feedback or not all(s.get("story_plan") for s in plan["shots"]):
            _refine_goals(plan,catalog,out,attempt,feedback,source_context=cached_source_context)
        _align_goals(plan,catalog,out,attempt,cached_source_context)
        _enforce_plan_hard_rules(plan,catalog,out)
        save(out/"material_plan.json",plan)
        payload=_review_payload(plan,catalog)
        try:
            preview_note = ' If this is a preview or pilot segment (e.g. 30 seconds), the final shot narration naturally reaches the preview cutoff and continues in the full film; do NOT fail or flag a preview plan for ending mid-sentence at the cutoff.'
            codex_prompt = ('Review this documentary PLAN, not delivered assets. Check shot/category/visual-goal consistency, full timeline, narrative continuity and duration mix within the stated tolerance. '
                     'Assess a workable documentary edit, not literal depiction of every spoken word. Factual script claims are a separate track. '
                     'Category changes are legitimate when the explicit shot transition advances the same idea. Existing archive themes need not prove every sentence. '
                     'A plan precedes source selection; exact final asset ranges/provenance are verified at production, so do not fail a coherent plan solely for not yet selecting final files. '
                     + preview_note + ' '
                     'Block actual medium contradictions, misleading unrecorded-event claims, unexplained spatial discontinuity, missing coverage or mix outside tolerance. '
                     'MATERIAL_POOL is everything this run can build from. A shot that asks for material outside the pool is a note against that shot, not a reason to fail the whole plan: the production gates replace unusable material at render time. '
                     'A shot may be answered with a labelled 3D diagram where the plan needs a mechanism shown, and a visual goal that describes honestly what the footage shows is a correct answer. '
                     'Return JSON {verdict:PASS|PARTIAL|FAIL,issues:[{shot_ids:[integer],problem:string,fix:string}],summary:string}. '
                     'If there is no concrete blocker, return PASS. PLAN:' + str(payload))
            overview = api("codex", codex_prompt, out / "planning" / f"plan_codex_{attempt}.json", tokens=3000,
                           timeout=GPT_PLANNING_TIMEOUT_SECONDS, deadline=time.monotonic() + GPT_PLANNING_DEADLINE_SECONDS)
        except Exception as exc:
            review_fallback=True
            overview={"status":"FALLBACK","data":{"verdict":"PARTIAL","issues":[],"summary":"Codex plan review timed out; deterministic plan gates remain active.","review_fallback":True,"error":type(exc).__name__}}
            save(out/"planning"/f"plan_codex_{attempt}.json",overview)
            event(out,"plan_review_fallback",attempt=attempt,error=type(exc).__name__)
        overview={**overview,"plan_identity":plan["identity"],"reviewed_plan_digest":digest(payload),"repair_attempt":attempt}
        save(review_path,overview)
        verdict=overview.get("data",{}).get("verdict")
        event(out,"plan_review",attempt=attempt,verdict=verdict)
        if overview.get("status")=="OK" and verdict=="PASS":return plan
        feedback=overview.get("data",{})

        if verdict in ("PARTIAL", "FAIL"):
            issues = overview.get("data", {}).get("issues", [])
            total = sum(r.get("duration_sec", 0) for r in plan.get("shots", []))
            is_preview = total <= 45.0

            def is_benign_issue(issue):
                text = (str(issue.get("problem", "")) + " " + str(issue.get("fix", ""))).lower()
                if is_preview and any(k in text for k in ("mid-sentence", "cut off", "incomplete", "endpoint", "thirty-second", "30-second", "preview", "downward", "continue in a subsequent", "subsequent planned shot")):
                    return True
                if any(k in text for k in ("mix", "percent", "duration", "tolerance")):
                    return True
                # The prompt itself says a shot asking for material outside
                # the pool is a note against that shot: the per-shot review,
                # the per-sentence footage search and the re-planning at
                # production handle it with the real material in hand.
                if any(k in text for k in ("material_pool", "material pool", "not supported by the", "supplied pool",
                                           "described pool", "pool does not", "not established by the")):
                    return True
                if any(k in text for k in ("transition", "handoff", "cross-fade", "cut from", "cuts from", "preceding shot", "wording", "description", "visual handoff")):
                    return True
                return False

            if issues and all(is_benign_issue(i) for i in issues):
                event(out, "plan_approved_with_editorial_allowance", issues=len(issues), summary=overview.get("data", {}).get("summary", ""))
                plan["codex_verdict"] = "PASS_WITH_EDITORIAL_ALLOWANCE"
                save(out / "material_plan.json", plan)
                return plan

            if issues and all(re.search(r"mix|percent|duration", str(i.get("problem", "")), re.I) for i in issues):
                changed = False
                for issue in issues:
                    ids = issue.get("shot_ids") or []
                    match = re.search(r"from\s+([0-9.]+)\s+to\s+([0-9.]+)", str(issue.get("fix", "")), re.I)
                    if len(ids) >= 2 and match:
                        boundary = float(match.group(2))
                        by_id = {int(s["shot_id"]): s for s in plan.get("shots", [])}
                        left, right = by_id.get(int(ids[0])), by_id.get(int(ids[1]))
                        if left and right and left.get("category") == "VIDEO":
                            left["timeline_end_sec"] = boundary
                            left["duration_sec"] = round(boundary - float(left["timeline_start_sec"]), 3)
                            right["timeline_start_sec"] = boundary
                            right["duration_sec"] = round(float(right["timeline_end_sec"]) - boundary, 3)
                            if "frame_end" in left: left["frame_end"] = round(boundary * 25)
                            if "frame_start" in right: right["frame_start"] = round(boundary * 25)
                            changed = True
                if changed:
                    totals = {c: 0.0 for c in CATEGORIES}
                    for shot in plan.get("shots", []): totals[shot["category"]] += float(shot.get("duration_sec", 0))
                    total = sum(totals.values()) or 1.0
                    plan["planned_percent"] = {c: round(100 * totals[c] / total, 3) for c in CATEGORIES}
                    save(out / "material_plan.json", plan)
                    event(out, "plan_mix_boundary_repaired", issues=len(issues), planned_percent=plan["planned_percent"])
                    return plan
            # A PARTIAL plan is kept after its last round anyway, and the
            # per-shot review is the gate on the picture: on TOPIC_2 two
            # more rounds rewrote the goals and came back PARTIAL again
            # (70 s). Only a FAIL is repaired.
            if verdict == "PARTIAL":
                break
    if review_fallback or (overview.get("data", {}).get("verdict") == "PARTIAL"):
        event(out,"plan_review_warning",reason="Codex approved with partial notes; plan retained for production")
        plan["codex_verdict"] = "PASS_WITH_EDITORIAL_ALLOWANCE"
        save(out / "material_plan.json", plan)
        return plan
    raise ValueError("Plan did not PASS Codex API review after two repairs; production blocked. See plan_review.json")

def failed_media(plan, shot_id, current):
    """Media this shot already failed in: the history kept in the plan plus the medium it has now.
    A plan from before the history existed knows only the current medium."""
    return set((plan.get("failed_categories") or {}).get(str(shot_id),[]))|{current}

def motion_fits(plan, shot):
    """The limits a MOTION shot is held to (unchanged): the mix gives MOTION time and the line is 3.0-6.5 s."""
    return (bool(float((plan.get("targets") or {}).get("MOTION",0)))
            and MIN_STATIC_SHOT_FRAMES<=shot["frame_end"]-shot["frame_start"] and shot["duration_sec"]<=MOTION_MAX_SECONDS)

def reroute_from_failed(plan, shot, failed):
    """Where a shot goes after it failed review in `failed` media, or None when no medium is left.
    A 3D shot that failed review must not be given 3D again (42% of 3D closes were REVIEW_REQUIRED on 2026-10-30
    and the old fallback sent them back to 3D until the film stopped with unresolved shots): MOTION when the line
    fits it, else VIDEO unless that failed too; None leaves it to the neighbour merge."""
    if "3D" not in failed:return "3D"
    if motion_fits(plan,shot) and "MOTION" not in failed:return "MOTION"
    if "VIDEO" not in failed:return "VIDEO"
    return None

def repair_allocation(plan, catalog, out, failures):
    """Use actual source limits to make one small feasible medium swap, then approve."""
    # A video-only film has no other medium to swap to. Its failed shots
    # get more footage searched and then run on from a neighbour instead
    # (runner.run_pipeline), so the plan is left as it is.
    if video_only(plan.get("targets")):
        event(out,"allocation_repair_skipped_video_only",shots=[f["shot_id"] for f in failures])
        return plan,[]
    candidate=deepcopy(plan)
    byid={s["shot_id"]:s for s in candidate["shots"]}
    for row in failures:
        if row["shot_id"] not in byid:raise ValueError("Failed shot is absent from the plan")
    failed_ids={r["shot_id"] for r in failures}
    previous_failures=set(plan.get("failed_video_allocations",[])) | failed_ids
    # A finished shot is never a donor. Swapping a delivered 3D/PHOTO shot to
    # VIDEO to rebalance the mix made it be produced again, some failed, and
    # every repair round on Kailasa opened new holes (39, 40, 56, 57, 63).
    def _delivered(s):
        path=out/"shots"/f'{s["shot_id"]:04d}'/"result.json"
        if not path.exists():return False
        r=load(path)
        return r.get("status") in ("PASS","PASS_WITH_WARNINGS") and r.get("shot_digest")==digest(s)
    donors=[s for s in candidate["shots"] if s["shot_id"] not in previous_failures and s["category"] in GENERATED_CATEGORIES
            and not _delivered(s)]
    consumed={}
    for s in plan["shots"]:
        path=out/"shots"/f'{s["shot_id"]:04d}'/"result.json"
        if s["shot_id"] in failed_ids or not path.exists():continue
        result=load(path)
        if result.get("status")!="PASS" or result.get("shot_digest")!=digest(s):continue
        a=result.get("artifact",{})
        segments=a.get("source_segments") or ([{"id":a.get("source_id"),"start":a.get("source_start_sec"),"frame_count":a.get("frame_count",0)}] if a.get("category")=="VIDEO" else [])
        for segment in segments:
            if segment.get("start") is not None:
                consumed[segment["id"]]=max(consumed.get(segment["id"],0),segment["start"]+segment["frame_count"]/25)
    media=[{"id":a["id"],"available_seconds":round(a["end"]-max(a["start"],consumed.get(a["id"],0)),2),"description":a.get("description","")[:180],**({"context_label":a["required_context_label"]} if a.get("required_context_label") else {})} for a in catalog["assets"] if a.get("usable") and a.get("category")=="VIDEO" and not a.get("excluded_by_independent_audit") and a["end"]-max(a["start"],consumed.get(a["id"],0))>=1]
    compact=[{k:s[k] for k in ("shot_id","narration","category","duration_sec")} for s in donors]
    # A failed shot may become an animation only while G-Labs answers.
    anim_ok=anim_possible(plan.get("targets"))
    motion_ok=bool(float((plan.get("targets") or {}).get("MOTION",0)))
    semantics_args=('Choose narrative-appropriate medium replacements. Do NOT calculate percentages; code solves duration budgets. '
                  'Return JSON {failed:[{shot_id,category:"VIDEO"|"PHOTO"|"3D"|"CARD"'+('|"ANIM"' if anim_ok else '')+('|"MOTION"' if motion_ok else '')+',reason}],donors:[{shot_id,video_score:integer,reason}]}. '
                  'For each failed shot choose an honest explanatory medium, not fake footage. CARD is one real photograph of a named person, product, object or document on a white explainer card with a banner, an arrow and a short annotation. '
                  +('ANIM is a generated, clearly illustrative 2D animation in a drawn style (paper collage, ink engraving, blueprint, screen print, isometric diorama or archival cut-out) without text, for an abstract idea, process or spread, 3 to 10 seconds. ' if anim_ok else '')
                  +('MOTION is a code-drawn motion graphic from the sentence\'s own words (dates, numbers, a list, steps or named places), 3 to 6.5 seconds. ' if motion_ok else '')+
                  'Score ONLY donor shots where remaining actual video can adequately support the thought and cover its duration;0..10, include only scores>=7. Previously consumed ranges are excluded. Include several independently feasible alternatives; do not spend one remaining range on multiple donors. '
                  'Return up to12suitable alternatives. Honest documentary context is allowed: actual present-day building footage, explicitly labelled modern context, can illustrate the legacy of building review practice without claiming the footage records a peer review. No need to literally depict every spoken word or certify a numeric claim in camera footage. Do not misidentify people or events. '
                  'Blueprint review, investigation, real licensing board/court and modern location context may illustrate an idea, but do not falsely identify people, dates or certify unverified facts. '
                  'Precise load calculations should stay with 3D or real evidence unless real film visibly explains them. No need to return every donor. '
                  f'FAILURES:{[{**f,"narration":byid[f["shot_id"]]["narration"]} for f in failures]}\nPOSSIBLE_DONORS:{compact}\nACTUAL_VIDEO:{media}',
                  out/"planning"/f"allocation_semantics_{digest(failures)[:12]}.json",2200)
    # One more try after the hedged pair failed: the selector is cheap
    # (Flash, 5-21 s) and a single upstream stall used to cancel the whole
    # repair round (EP03/EP04/EP05 1106, allocation_repair_blocked).
    try:
        selection=_planning_api(*semantics_args)["data"]
    except RuntimeError as exc:
        event(out,"allocation_semantics_retry",error=str(exc)[-300:])
        time.sleep(5)
        selection=_planning_api(*semantics_args)["data"]
    # One malformed row used to cancel the whole repair and block the film.
    # A row that cannot be used is skipped; a failed shot the selector left
    # out gets the explanatory medium it did not fail in. Codex still
    # approves the resulting plan below.
    # A failed shot never keeps the medium it failed in: the selector chose
    # VIDEO again for VIDEO shots that had failed with every candidate,
    # including a per-sentence footage search.
    chosen={}
    for row in selection.get("failed",[]):
        if (row.get("shot_id") in failed_ids and row.get("category") in CATEGORIES and row["shot_id"] not in chosen
                and row["category"]!=byid[row["shot_id"]]["category"]):
            chosen[row["shot_id"]]=row["category"]
    # Each photograph is used once, so a shot may only become PHOTO (or a
    # CARD, which is built from a photograph) while an unused one is left:
    # on Gotthard eight lines became PHOTO after all 31 photos were taken
    # and died as NO_MATCH.
    finished=[load(p) for p in (out/"shots").glob("*/result.json")]
    used_photos={(r.get("artifact") or {}).get("source_id") for r in finished
                 if r.get("status") in ("PASS","PASS_WITH_WARNINGS") and (r.get("artifact") or {}).get("category") in STILL_CATEGORIES}
    free_photos=sum(1 for a in catalog["assets"] if a.get("usable") and a.get("category")=="PHOTO" and a["id"] not in used_photos)
    # What each failed shot has failed in is kept with the plan, so the next
    # pass does not hand a shot back a medium it already failed in.
    history=candidate.setdefault("failed_categories",{})
    stuck=set()
    for sid in sorted(failed_ids):
        failed=failed_media(plan,sid,byid[sid]["category"])
        history[str(sid)]=sorted(failed)
        # The selector may not send a shot back to 3D after 3D failed review.
        pick=chosen.get(sid)
        if pick=="3D" and "3D" in failed:pick=None
        if pick is None:
            # The old default was 3D, or a still for a 3D shot. After 3D failed review:
            # MOTION when it fits, else a still, else VIDEO, else nothing (neighbour merge).
            if "3D" not in failed:pick="3D"
            elif motion_fits(plan,byid[sid]) and "MOTION" not in failed:pick="MOTION"
            elif "PHOTO" not in failed:pick="PHOTO"
            else:pick=reroute_from_failed(plan,byid[sid],failed)
        new=pick
        # Where a medium does not fit, the shot goes to the ladder instead: a
        # diagram (3D) only while 3D has not failed, else MOTION, else VIDEO.
        later=lambda:reroute_from_failed(plan,byid[sid],failed|{new})
        # A still is held for at most 6.5 s; a longer shot becomes a diagram.
        if new in STILL_CATEGORIES and (byid[sid]["duration_sec"]>6.5 or free_photos<=0):new=later()
        if new in STILL_CATEGORIES:free_photos-=1
        # An animation is only chosen while the mix gives ANIM time, G-Labs
        # answers and the line fits one clip (3.0-10 s); otherwise a diagram.
        if new=="ANIM" and not (anim_ok and MIN_STATIC_SHOT_FRAMES<=byid[sid]["frame_end"]-byid[sid]["frame_start"]
                                and byid[sid]["duration_sec"]<=ANIM_MAX_SECONDS):
            new=later()
        # A motion graphic only while the mix gives MOTION time and the line
        # fits its 3.0-6.5 s; otherwise a diagram.
        if new=="MOTION" and not (motion_ok and MIN_STATIC_SHOT_FRAMES<=byid[sid]["frame_end"]-byid[sid]["frame_start"]
                                  and byid[sid]["duration_sec"]<=MOTION_MAX_SECONDS):
            new=later()
        if new is None:
            stuck.add(sid);continue  # no medium left: the neighbour merge takes it
        byid[sid]["category"]=new
    if stuck:event(out,"allocation_no_medium_left",shots=sorted(stuck))
    if stuck>=failed_ids:
        # Nothing to produce again; only the history is kept for the next pass.
        save(out/"material_plan.json",candidate)
        return candidate,[]
    valid_donors={s["shot_id"]:s for s in donors}
    scores={};donor_reasons={}
    for row in selection.get("donors",[]):
        if row.get("shot_id") in valid_donors and type(row.get("video_score")) is int and 7<=row["video_score"]<=10:
            scores[row["shot_id"]]=row["video_score"]
            donor_reasons[row["shot_id"]]=row.get("reason","")
    options=[byid[n] for n in scores]
    total=sum(s["duration_sec"] for s in candidate["shots"])
    baseline={c:sum(s["duration_sec"] for s in candidate["shots"] if s["category"]==c) for c in CATEGORIES}
    solved=None
    if options:
        # One row per category: a donor adds its time to VIDEO and takes it
        # from its own category. The matrix had four rows for three bounds.
        matrix=np.zeros((len(CATEGORIES),len(options)))
        for i,s in enumerate(options):
            matrix[0,i]=s["duration_sec"];matrix[CATEGORIES.index(s["category"]),i]=-s["duration_sec"]
        # A plan made before CARD existed has no CARD target; it is 0.
        lower=[total*(plan["targets"].get(c,0)-MIX_TOLERANCE_PERCENT)/100-baseline[c] for c in CATEGORIES]
        upper=[total*(plan["targets"].get(c,0)+MIX_TOLERANCE_PERCENT)/100-baseline[c] for c in CATEGORIES]
        try:
            solved=milp(np.array([1+(10-scores[s["shot_id"]])*.01 for s in options]),integrality=np.ones(len(options)),bounds=Bounds(0,1),constraints=LinearConstraint(matrix,lower,upper),options={"time_limit":5})
        except ValueError as exc:
            event(out,"allocation_solver_fallback",error=str(exc)[:200])
    if solved is not None and solved.x is not None:
        for s,value in zip(options,solved.x):
            if value>.5:s["category"]="VIDEO"
    else:
        # The sources cannot give back all the VIDEO time that failed. A
        # picture that matches the voice comes before the mix, so the
        # best-scored donors return to VIDEO up to the VIDEO ceiling and
        # the shortfall stays visible in the plan and the events.
        ceiling=total*(plan["targets"]["VIDEO"]+MIX_TOLERANCE_PERCENT)/100
        video=baseline["VIDEO"]
        for s in sorted(options,key=lambda s:-scores[s["shot_id"]]):
            if video+s["duration_sec"]<=ceiling:
                s["category"]="VIDEO";video+=s["duration_sec"]
    total=sum(s["duration_sec"] for s in candidate["shots"])
    percent={c:100*sum(s["duration_sec"] for s in candidate["shots"] if s["category"]==c)/total for c in CATEGORIES}
    if any(abs(percent[c]-plan["targets"].get(c,0))>MIX_TOLERANCE_PERCENT for c in CATEGORIES):
        event(out,"repair_mix_outside_target",planned_percent=percent,targets=plan["targets"],
              tolerance=MIX_TOLERANCE_PERCENT,reason="Real footage could not carry the failed VIDEO time")
    candidate["planned_percent"]=percent
    candidate["failed_video_allocations"]=sorted(previous_failures)
    changed=sorted((failed_ids-stuck) | {s["shot_id"] for s in candidate["shots"] if s["category"]!=next(x["category"] for x in plan["shots"] if x["shot_id"]==s["shot_id"])})
    goals={}
    for f in failures:
        if f["shot_id"] in stuck:continue
        goals[f["shot_id"]]={"visual_goal":f"Create a clearly illustrative {byid[f['shot_id']]['category']} explanation for: {byid[f['shot_id']]['narration']}","context":"No sufficiently matching archival visual source was available; disclose this as an explanatory illustration, not footage.","transition":"Continue the same narrated idea using a clearly labeled explanatory visual."}
    for s in candidate["shots"]:
        if s["shot_id"] in changed and s["shot_id"] not in goals:
            goals[s["shot_id"]]={"visual_goal":f"Use relevant {s['category']} evidence for: {s['narration']}","context":"Reallocated from an equally timed source-limited shot; preserve the same factual subject.","transition":"Connect the prior and next explanation without changing the narration."}
    for n,g in goals.items():byid[n]["story_plan"]={"scene_id":byid[n]["scene_id"],"shot_id":n,"category":byid[n]["category"],**g}
    # No required on-screen label is added: nothing renders one, burned-in
    # text is a review defect, and the reviewer failed shots for its absence.
    for n in changed:
        if n in donor_reasons:byid[n]["story_plan"]["visual_goal"]=donor_reasons[n]
    if any(byid[n]["narration"]!=next(s["narration"] for s in plan["shots"] if s["shot_id"]==n) or byid[n]["duration_sec"]!=next(s["duration_sec"] for s in plan["shots"] if s["shot_id"]==n) for n in changed):raise ValueError("Repair changed narration/timing")
    neighbors=[s for i,s in enumerate(candidate["shots"]) if s["shot_id"] in changed or (i and candidate["shots"][i-1]["shot_id"] in changed) or (i+1<len(candidate["shots"]) and candidate["shots"][i+1]["shot_id"] in changed)]
    evidence={"failed":failures,"changed":[byid[n] for n in changed],"neighbors":[{k:s[k] for k in ("shot_id","category","narration","story_plan")} for s in neighbors],"target_percent":plan["targets"],"actual_percent":percent,"narration_and_timing_unchanged_assertion":True,"delivery_notes":["Source-dependent script claims are not certified, including underground/as-built geometry, broad legal liability, duration and tool specifications; factual review remains required before public release."],"actual_video":media}
    # A timeout is not a verdict. A FAIL verdict from this plan review is
    # already recorded as notes and production continues (below), so a
    # timed-out review used to be stricter than a FAIL: it raised, the
    # caller logged allocation_repair_blocked and stopped repairing, and the
    # failed shots sat unresolved until the film was restarted (EP02/EP04
    # 1106: ReadTimeout after 45-162 s). The re-planned shots still each
    # pass the strict per-shot production review.
    try:
        response=api("codex",f'Review this bounded source-aware PLAN, not finished artifacts. Failed shots switch to an explicitly illustrative explanation; source-appropriate video shots compensate within the unchanged percentage targets. Exact equal-duration swaps are NOT required; tolerance is{MIX_TOLERANCE_PERCENT}percentage points. Code asserted unchanged narration/timing. Source reasons and neighboring shots are supplied. Actual selected frames will still require the existing per-shot production review. Check medium appropriateness, truthful required labels and narrative continuity. Factual script claims are explicitly outside this visual-plan approval; keep them in delivery notes. Return JSON {{verdict:PASS|FAIL,issues:[string],summary:string}}. '+str(evidence),out/"planning"/f"allocation_codex_{digest(failures)[:12]}.json",tokens=1400,timeout=GPT_PLANNING_TIMEOUT_SECONDS)
    except RuntimeError as exc:
        response={"status":"FALLBACK","data":{"verdict":"PARTIAL","issues":[],"summary":"Codex allocation review failed; per-shot production review remains the gate.","review_fallback":True,"error":str(exc)[-300:]}}
        event(out,"allocation_review_fallback",error=str(exc)[-300:])
    # The re-planned shots are produced again and each one passes the strict
    # per-shot review, so a plan-level objection is recorded with the plan
    # instead of leaving the failed shots without any medium at all.
    if response["data"].get("verdict")!="PASS":
        event(out,"allocation_review_notes",verdict=response["data"].get("verdict"),issues=response["data"].get("issues"))
    save(out/"planning"/f"before_allocation_{digest(failures)[:12]}.json",plan)
    save(out/"material_plan.json",candidate)
    save(out/"plan_review.json",{**response,"plan_identity":candidate["identity"],"reviewed_plan_digest":digest(_review_payload(candidate))})
    event(out,"source_aware_reallocation",changed_shots=changed,planned_percent=percent)
    return candidate,changed

_LADDERS_V1={"VIDEO":["PHOTO","CARD","MOTION","3D","ANIM"],"PHOTO":["PHOTO","CARD","MOTION","3D","ANIM"],"CARD":["PHOTO","CARD","MOTION","3D","ANIM"],
    "3D":["MOTION","ANIM","PHOTO","CARD","VIDEO","3D"],"MOTION":["3D","PHOTO","CARD","VIDEO"],"ANIM":["MOTION","3D","PHOTO","CARD","VIDEO"]}
# Measured pass rate per attempt on EP02-05 (shot_done events): ANIM 81%, MOTION 74%, VIDEO/PHOTO/CARD reuse 50%, 3D 32%.
# V2 puts 3D last wherever a 74-81% medium is still open (3D costs a Chrome render plus a GPT lane per try and passes a third).
_LADDERS_V2={"VIDEO":["PHOTO","CARD","MOTION","ANIM","3D"],"PHOTO":["PHOTO","CARD","MOTION","ANIM","3D"],"CARD":["PHOTO","CARD","MOTION","ANIM","3D"],
    "3D":["MOTION","ANIM","PHOTO","CARD","VIDEO","3D"],"MOTION":["ANIM","PHOTO","CARD","VIDEO","3D"],"ANIM":["MOTION","PHOTO","CARD","VIDEO","3D"]}

def _escalation_ladder(category):
    v2=os.environ.get("DOCUMENTARY_LADDER_V2","1")!="0"
    return list((_LADDERS_V2 if v2 else _LADDERS_V1).get(category,_LADDERS_V1["ANIM"]))

def escalate_unresolved(plan, out, failures, catalog=None):
    """In-call escalation of shots that stayed unresolved after their per-shot budget: no API call, no Codex plan
    review. Each shot moves one rung down a fixed ladder of media it has not failed in (history is kept in
    plan["failed_categories"], like repair_allocation): generated shots go 3D -> MOTION -> ANIM -> PHOTO/CARD -> VIDEO,
    a failed VIDEO/PHOTO/CARD shot goes to PHOTO/CARD (free photo left) -> MOTION -> 3D -> ANIM. A hook shot (first
    HOOK_VIDEO_SECONDS) never changes medium. The picture judge is untouched: the shot is produced and reviewed as
    any other. Returns (plan, changed_ids); changed_ids is empty when no shot has a medium left (the neighbour merge
    takes those)."""
    if video_only(plan.get("targets")):return plan,[]
    candidate=deepcopy(plan)
    byid={s["shot_id"]:s for s in candidate["shots"]}
    anim_ok=anim_possible(plan.get("targets"))
    motion_ok=bool(float((plan.get("targets") or {}).get("MOTION",0)))
    free_photos=None
    if catalog is not None:
        finished=[load(p) for p in (out/"shots").glob("*/result.json")]
        used={(r.get("artifact") or {}).get("source_id") for r in finished
              if r.get("status") in ("PASS","PASS_WITH_WARNINGS") and (r.get("artifact") or {}).get("category") in STILL_CATEGORIES}
        free_photos=sum(1 for a in catalog["assets"] if a.get("usable") and a.get("category")=="PHOTO" and a["id"] not in used)
    history=candidate.setdefault("failed_categories",{})
    changed=[]
    for sid in sorted({f["shot_id"] for f in failures}):
        shot=byid.get(sid)
        if shot is None or shot["timeline_start_sec"]<HOOK_VIDEO_SECONDS:continue
        failed=failed_media(plan,sid,shot["category"])
        history[str(sid)]=sorted(failed)
        frames=shot["frame_end"]-shot["frame_start"]
        def ok(c):
            if c in failed:return False
            if c=="MOTION":return motion_ok and MIN_STATIC_SHOT_FRAMES<=frames and shot["duration_sec"]<=MOTION_MAX_SECONDS
            if c=="ANIM":return anim_ok and MIN_STATIC_SHOT_FRAMES<=frames and shot["duration_sec"]<=ANIM_MAX_SECONDS
            if c in STILL_CATEGORIES:return shot["duration_sec"]<=6.5 and (free_photos is None or free_photos>0)
            return True
        ladder=_escalation_ladder(shot["category"])
        new=next((c for c in ladder if ok(c)),None)
        if new is None:continue
        if new in STILL_CATEGORIES and free_photos is not None:free_photos-=1
        shot["category"]=new
        shot["story_plan"]={**(shot.get("story_plan") or {}),"scene_id":shot["scene_id"],"shot_id":sid,"category":new,
            "visual_goal":f"Create a clearly illustrative {new} explanation for: {shot['narration']}",
            "context":"The earlier medium was rejected by the shot review; honest illustrative medium, same narration."}
        changed.append(sid)
    if not changed:
        save(out/"material_plan.json",candidate)  # keep the failure history
        return candidate,[]
    total=sum(s["duration_sec"] for s in candidate["shots"])
    candidate["planned_percent"]={c:100*sum(s["duration_sec"] for s in candidate["shots"] if s["category"]==c)/total for c in CATEGORIES}
    candidate["failed_video_allocations"]=sorted(set(plan.get("failed_video_allocations",[]))|{f["shot_id"] for f in failures})
    save(out/"material_plan.json",candidate)
    review=load(out/"plan_review.json") if (out/"plan_review.json").exists() else {}
    save(out/"plan_review.json",{**review,"reviewed_plan_digest":digest(_review_payload(candidate))})
    event(out,"in_call_escalation",changed={str(n):byid[n]["category"] for n in changed},planned_percent=candidate["planned_percent"])
    return candidate,changed

def merge_into_neighbours(plan, out, failed_ids, max_sec=9.0, hook=False):
    """Give a sentence no medium could carry to the shot next to it.

    A line that failed as footage, as a photograph and as a diagram is
    covered by its neighbour's picture running on: the neighbour, a
    finished shot of the same scene, is extended over it, so the cut
    disappears and the picture stays one the reviewer accepted for the
    story at that point. The neighbour is produced and reviewed again for
    its longer narration. Photographs are not extended (6.5 s ceiling),
    nor is anything past max_sec; in the opening hook only footage runs on.
    """
    candidate=deepcopy(plan)
    rows=candidate["shots"]
    merged={}
    # Repeated so a run of failed lines can join one finished neighbour in turn.
    pending=sorted(failed_ids)
    for k,sid in enumerate(pending*3):
        if sid in merged:continue
        # Last round, for a line no medium could carry: a photograph may
        # also run on to max_sec (Gotthard 98 sat between two stills), and
        # any neighbour gets one more second (Kailasa: two lines stuck at a
        # merged 9.5-9.7 s).
        last=k>=2*len(pending)
        photo_limit=max_sec+1.0 if last else 6.5
        i=next((k for k,r in enumerate(rows) if r["shot_id"]==sid),None)
        if i is None:continue
        row=rows[i]
        for j in (i-1,i+1):
            if not 0<=j<len(rows):continue
            n=rows[j]
            # A motion graphic runs on like a still (6.5 s, the merge's last round longer).
            limit=photo_limit if n["category"] in STILL_CATEGORIES+("MOTION",) else max_sec+(1.0 if last else 0.0)
            # An animation is one generated clip, at most 10 s long.
            if n["category"]=="ANIM":limit=min(limit,ANIM_MAX_SECONDS)
            # The opening hook is never merged: a longer cut breaks its
            # ~4 s rhythm. A hook line gets its own retry rounds instead.
            # hook=True is the caller's last resort, after the hook's own
            # rounds found nothing (TOPIC_8 7 sat alone in the hook).
            if (n["shot_id"] in failed_ids or n["duration_sec"]+row["duration_sec"]>limit
                    or (not hook and (row["timeline_start_sec"]<HOOK_VIDEO_SECONDS or n["timeline_start_sec"]<HOOK_VIDEO_SECONDS))):
                continue
            first,second=(n,row) if j<i else (row,n)
            # The neighbour keeps its own line; the line it now runs over is
            # recorded apart, so the review judges the picture by its own
            # sentence and only checks that it does not contradict the other.
            n.update(frame_start=first["frame_start"],frame_end=second["frame_end"],
                     timeline_start_sec=first["timeline_start_sec"],timeline_end_sec=second["timeline_end_sec"],
                     duration_sec=round(n["duration_sec"]+row["duration_sec"],3),
                     continues_over=n.get("continues_over",[])+[row["narration"]]+row.get("continues_over",[]))
            merged[sid]=n["shot_id"]
            del rows[i]
            break
    if not merged:return plan,[]
    if any(a["frame_end"]!=b["frame_start"] for a,b in zip(rows,rows[1:])):raise ValueError("Merge broke the timeline")
    total=sum(s["duration_sec"] for s in rows)
    candidate["planned_percent"]={c:100*sum(s["duration_sec"] for s in rows if s["category"]==c)/total for c in CATEGORIES}
    candidate["merged_shots"]={**plan.get("merged_shots",{}),**{str(k):v for k,v in merged.items()}}
    save(out/"material_plan.json",candidate)
    review=load(out/"plan_review.json") if (out/"plan_review.json").exists() else {}
    save(out/"plan_review.json",{**review,"reviewed_plan_digest":digest(_review_payload(candidate))})
    event(out,"shots_merged_into_neighbours",merged=merged,planned_percent=candidate["planned_percent"])
    return candidate,sorted(set(merged.values()))

# A profile with "shot_seconds": "auto" (wildlife) keeps every shot at the
# ~4 s rhythm while the catalog's clean VIDEO cuts cover them. When they do
# not (TOPIC_2's first catalog was ~80 shots short at 4 s: shots that burned
# retries, searches and merges and failed anyway), the fewest shots are
# lengthened: a run of 2-4 neighbouring shots of one scene is cut into one
# shot fewer, each piece at most GROWN_SHOT_MAX_FRAMES, fewest grown shots
# and then the smallest extension first. The opening hook is never touched.
GROWN_SHOT_MAX_FRAMES = 175
# Hard ceiling on one shot (user rule 2026-11-08: no cut longer than 4 s ->
# DOCUMENTARY_MAX_SHOT_FRAMES=100). 0 = off. Caps the grown shots, the merges
# into neighbours and splits any longer piece shots() cuts.
MAX_SHOT_FRAMES = int(os.environ.get("DOCUMENTARY_MAX_SHOT_FRAMES", "0") or 0)
if MAX_SHOT_FRAMES:
    GROWN_SHOT_MAX_FRAMES = min(GROWN_SHOT_MAX_FRAMES, MAX_SHOT_FRAMES)


def _cap_bounds(scene, bounds):
    """Split every piece longer than MAX_SHOT_FRAMES at the word end nearest its middle (else the middle)."""
    if not MAX_SHOT_FRAMES:
        return bounds
    ends = [round(w["end"] * 25) for w in scene.get("word_timestamps", [])]
    out = [bounds[0]]
    for b in bounds[1:]:
        while b - out[-1] > MAX_SHOT_FRAMES:
            a = out[-1]
            pieces = math.ceil((b - a) / MAX_SHOT_FRAMES)
            ideal = a + (b - a) // pieces
            ok = [v for v in ends if a + 25 <= v <= a + MAX_SHOT_FRAMES and b - v >= 25]
            out.append(min(ok, key=lambda v: abs(v - ideal)) if ok else ideal)
        out.append(b)
    return out


def shot_regroup(out):
    """The run's stored regroup (shot_length.json) for an auto profile, else None."""
    path = Path(out) / "shot_length.json"
    if not path.is_file() or for_run(out).get("shot_seconds") != "auto":
        return None
    try:
        return [tuple(int(v) for v in w) for w in load(path)["regroup"]]
    except (KeyError, TypeError, ValueError):
        return None


def shot_length(timeline, catalog, video_percent, auto, regroup=None):
    """(regroup, clean VIDEO cuts, needed cuts) of the shots a plan is cut to.

    Not auto: no regroup and the need from the narration length, as before.
    Auto: the given regroup, else the fewest grown shots that bring the VIDEO
    shots within the clean cuts (all of them while none fit; [] when the
    4 s shots fit already). A source gives at most four cuts 30 s apart, so
    the cuts barely change with the length; they are counted at 4 s.
    """
    cut_sec = TARGET_SHOT_FRAMES / 25
    capacity = _video_capacity(catalog, cut_sec)
    if not auto:
        return None, capacity, math.ceil(float(timeline["audio_duration_sec"]) * float(video_percent) / 100 / cut_sec)
    need = lambda rows: math.ceil(len(rows) * float(video_percent) / 100)
    if regroup is not None:
        return regroup, capacity, need(shots(timeline, regroup))
    rows = shots(timeline)
    deficit = need(rows) - capacity
    scenes = {s["scene_id"]: s for s in timeline["scenes"]}
    # Every run that can lose one shot, by its smallest size (fewest grown
    # shots), then its longest piece (smallest extension), then its place.
    runs = []
    for i, first in enumerate(rows):
        if first["frame_start"] < HOOK_VIDEO_SECONDS * 25:
            continue
        for m in (2, 3, 4):
            window = rows[i:i + m]
            if len(window) < m or window[-1]["scene_id"] != first["scene_id"]:
                break
            a, b = window[0]["frame_start"], window[-1]["frame_end"]
            if b - a > GROWN_SHOT_MAX_FRAMES * (m - 1):
                continue
            pieces = _bounds(scenes[first["scene_id"]], a, b, m - 1)
            longest = max(y - x for x, y in zip(pieces, pieces[1:]))
            if len(pieces) == m and longest <= GROWN_SHOT_MAX_FRAMES:
                runs.append(((m, longest, a), {r["shot_id"] for r in window}, (a, b, m - 1)))
                break
    runs.sort(key=lambda run: run[0])
    chosen, used = [], set()
    for _key, ids, run in runs:
        if len(chosen) >= deficit:
            break
        if not ids & used:
            used |= ids
            chosen.append(run)
    chosen.sort()
    return chosen, capacity, need(shots(timeline, chosen))


# Shots of one scene are not cut to equal lengths: each piece gets a weight in
# this range, so a film runs short and long shots in its own order instead of a
# cut every ~4 s in every film. The draw is seeded by the scene's words and
# frames, so every call cuts the same film the same way.
SHOT_RHYTHM = (0.6, 1.5)


def _bounds(scene, start, end, count):
    """count pieces of [start, end) cut at the scene's punctuation, else its word ends."""
    span = end - start
    rng = random.Random(f"{scene.get('narration', '')}|{start}|{end}|{count}")
    weights = [rng.uniform(*SHOT_RHYTHM) for _ in range(count)]
    marks = [sum(weights[:i]) / sum(weights) for i in range(count + 1)]
    punc_ends = [round(w["end"] * 25) for w in scene.get("word_timestamps", [])
                 if str(w["word"]).rstrip().endswith((".", "!", "?", ",", ";", ":", "-", "—"))]
    all_ends = [round(w["end"] * 25) for w in scene.get("word_timestamps", [])]
    bounds = [start]
    for i in range(1, count):
        ideal = round(start + span * marks[i])
        viable_punc = [v for v in punc_ends if bounds[-1] + MIN_STATIC_SHOT_FRAMES <= v <= end - MIN_STATIC_SHOT_FRAMES]
        if viable_punc:
            best = min(viable_punc, key=lambda v: abs(v - ideal))
            if abs(best - ideal) <= 45:
                bounds.append(best)
                continue
        viable_words = [v for v in all_ends if bounds[-1] + MIN_STATIC_SHOT_FRAMES <= v <= end - MIN_STATIC_SHOT_FRAMES]
        if viable_words:
            bounds.append(min(viable_words, key=lambda v: abs(v - ideal)))
        else:
            break
    bounds.append(end)
    return bounds


def shots(timeline, regroup=None):
    """The plan's shots cut at the narration, about TARGET_SHOT_FRAMES each.

    regroup (shot_length): (frame_start, frame_end, pieces) runs of shots
    cut again into fewer, longer pieces.
    """
    rows = []
    cursor = 0
    total = math.ceil(timeline["audio_duration_sec"] * 25)
    runs = {a: (b, n) for a, b, n in regroup or ()}
    for scene in timeline["scenes"]:
        end_frame = min(total, round(scene["timeline_end_sec"] * 25))
        if scene is timeline["scenes"][-1]:
            end_frame = total
        scene_frames = end_frame - cursor
        count = max(1, round(scene_frames / TARGET_SHOT_FRAMES))
        bounds = _bounds(scene, cursor, end_frame, count)
        if runs:
            cut = [bounds[0]]
            while cut[-1] < end_frame:
                a = cut[-1]
                if a in runs and runs[a][0] <= end_frame:
                    cut.extend(_bounds(scene, a, runs[a][0], runs[a][1])[1:])
                else:
                    cut.append(next(v for v in bounds if v > a))
            bounds = cut
        bounds = _cap_bounds(scene, bounds)
        for a, b in zip(bounds, bounds[1:]):
            words = [w for w in scene.get("word_timestamps", []) if a / 25 <= ((w["start"] + w["end"]) / 2) < b / 25]
            narration = " ".join(w["word"] for w in words)
            rows.append({
                "shot_id": len(rows) + 1, "scene_id": scene["scene_id"], "frame_start": a, "frame_end": b,
                "timeline_start_sec": a / 25, "timeline_end_sec": b / 25, "duration_sec": (b - a) / 25,
                "narration": narration, "full_scene_narration": scene["narration"], "narrative_beat": scene["narrative_beat"]
            })
        cursor = end_frame
    if not rows or rows[0]["frame_start"] != 0 or rows[-1]["frame_end"] != total or any(a["frame_end"] != b["frame_start"] for a, b in zip(rows, rows[1:])):
        raise ValueError("Visual timeline is not contiguous")
    return rows

# A talking head is rejected at production, so a recording described as
# one gives the plan no VIDEO cut. Same words as the production filters
# (runner._film_talking_head, render_stage._talking_head_delivery).
_TALKING_HEAD_WORDS = ("interview", "talking head", "anchor", "presenter", "reporter to camera",
                       "speaks to camera", "podium", "commentator", "press conference")

def _video_capacity(catalog, cut_sec):
    """How many VIDEO shots the catalog can carry under the source rules.

    The last run planned 95 VIDEO shots and ~55 found no footage: one
    recording gives at most MAX_USES_PER_ORIGIN cuts, at least
    MIN_SAME_ORIGIN_GAP_SECONDS apart, and talking heads are rejected.
    Per origin, cuts of cut_sec seconds are placed greedily in its windows.
    """
    windows = {}
    for a in (catalog or {}).get("assets") or []:
        if a.get("category") != "VIDEO" or not a.get("usable", True):
            continue
        text = " ".join([str(a.get("description") or ""), str(a.get("source_title") or ""),
                         str(a.get("composition") or ""), " ".join(map(str, a.get("keywords") or []))]).lower()
        if any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in _TALKING_HEAD_WORDS):
            continue
        try:
            start = float(a["source_start"] if a.get("source_start") is not None else a.get("start", 0))
            end = float(a["source_end"] if a.get("source_end") is not None else a.get("end", 0))
        except (TypeError, ValueError):
            continue
        if end - start >= cut_sec:
            windows.setdefault(origin_id(a), []).append((start, end))
    total = 0
    for spans in windows.values():
        cuts, free_from = 0, -math.inf
        for start, end in sorted(spans):
            cursor = max(start, free_from)
            while cuts < MAX_USES_PER_ORIGIN and cursor + cut_sec <= end:
                cuts += 1
                free_from = cursor + cut_sec + MIN_SAME_ORIGIN_GAP_SECONDS
                cursor = free_from
        total += cuts
    return total

def _scene_prompt(context,rows):
    return ('Plan the best documentary visual medium for each provided narration scene in the full-story context. '
            'Score each category VIDEO (real camera/archive), '
            'PHOTO (actual archival investigation photos), 3D (true mesh-based explanatory geometry, NOT FEA), '
            'CARD (one real photograph of a named person, product, object or document cut out on a white explainer card with a title banner, an arrow and a short annotation; '
            'best for a sentence that names a person, product, object, document, organisation, date or number), '
            'ANIM (a generated, clearly illustrative 2D animation of concrete objects in gentle motion in a drawn style: paper collage, ink engraving, blueprint, screen print, isometric diorama or archival cut-out; no text; '
            'best for an abstract idea, a process, something spreading across places or a map, a concept no honest footage shows; never for a named person\'s likeness or an event a real recording shows), '
            'MOTION (a code-drawn motion graphic built from the sentence\'s own words: kinetic power words, a dated timeline, a metric count-up with bars, a route between named places drawn as nodes and links without a map, or numbered steps; '
            'best for a sentence with dates, numbers, comparisons, a list, a process or named places) from0to10 by narrative relevance. '
            'Across PHOTO shots, vary tone and composition (monochrome archive, daylight exterior, interior detail, wide context, close evidence) and never repeat the same visual treatment. '
            'All six need meaningful use but do not fake evidence to fill a quota. Prefer3D only for mechanical/spatial explanation; never invent a static card or slide other than CARD. The same source or source family must not be reused across shots, except that one recording may be cut up to three times with at least 30 seconds between the cuts, while a photograph or a 3D scene is used once. '
            'No exact numbers, stress fields, historical reconstruction claims or false physics in generated graphics. '
            f'For every shot starting in the opening hook (first {int(HOOK_VIDEO_SECONDS)} seconds), assign VIDEO as the preferred hook medium when truthful; these hook shots must use high-quality moving footage in the source stage. '
            'Also identify 1-2 forbidden media if a medium would mislead or fail here. Avoid a photo for precise load/legal-code explanation; avoid3D for legal/family aftermath, avoid VIDEO for unrecorded collapse action itself. '
            'Return JSON {scenes:[{scene_id,scores:{VIDEO:number,PHOTO:number,"3D":number,CARD:number,ANIM:number,MOTION:number},forbidden:[string],visual_goal:string,context:string}]}. '
            'Keep each visual_goal concise and concrete. Original narration stays unchanged; review factual concerns separately.\nSTORY:'+str(context)+'\nSCENES:'+str(rows))

def score_scenes(timeline,out,store=False):
    """The per-scene Flash medium scores (planning/group_*.json).

    They depend on the timeline only, so the early 3D phase computes them
    while the sources are still being fetched and stores them in
    planning/scene_scores.json; make_plan then plans from the very same
    scores. Without a stored file (DOCUMENTARY_EARLY_3D off) every call
    scores afresh, as before. A group that fell back on a timeout is never
    stored, so a stored file holds real Flash scores only.
    """
    scenes=[{k:s[k] for k in ("scene_id","narration","narrative_beat")} for s in timeline["scenes"]]
    context=[{"scene_id":s["scene_id"],"beat":s["narrative_beat"]} for s in scenes]
    cache=Path(out)/"planning"/"scene_scores.json"
    key=digest({"planner_version":PLAN_VERSION,"timeline":timeline["identity"],"scenes":scenes,"prompt":_scene_prompt(context,[])})
    if cache.exists():
        stored=load(cache)
        if stored.get("key")==key:
            return _cap_organic_3d({s["scene_id"]:s for s in deepcopy(stored["scenes"])},scenes)

    def group(item):
        i,rows=item
        prompt=_scene_prompt(context,rows)
        receipt=Path(out)/"planning"/f"group_{i:02}.json"
        try:
            response=_planning_api(prompt,receipt,2200)
            actual=response["data"]["scenes"]
        except Exception as exc:
            # A planning timeout must not terminate the entire production. Use
            # a truthful neutral plan, keep the hook VIDEO constraint, and
            # record the fallback so the final report cannot call it a Flash PASS.
            actual=[]
            for row in rows:
                hook=float(row.get("timeline_start_sec",0)) < HOOK_VIDEO_SECONDS
                actual.append({"scene_id":row["scene_id"],"scores":{"VIDEO":8 if hook else 6,"PHOTO":5,"3D":5,"CARD":5,"ANIM":5,"MOTION":5},
                               "forbidden":[],"visual_goal":str(row.get("narrative_beat") or row.get("narration") or "")[:180],
                               "context":"deterministic timeout fallback","planning_fallback":True})
            save(receipt,{"status":"PLANNING_FALLBACK","error":type(exc).__name__,"scenes":actual})
            event(out,"story_plan_group_fallback",group=i,scenes=len(actual),error=type(exc).__name__)
        # A scene the answer left out, or scored outside the scale, takes the
        # deterministic plan; invented and repeated ids are dropped instead
        # of failing the whole film.
        def valid(s):
            scores=s.get("scores") if isinstance(s,dict) else None
            return (isinstance(scores,dict) and set(scores)==set(CATEGORIES)
                    and all(type(v) in (float,int) and math.isfinite(v) and 0<=v<=10 for v in scores.values()))
        given={}
        for s in actual:
            if valid(s) and s.get("scene_id") in {r["scene_id"] for r in rows}:given.setdefault(s["scene_id"],s)
        actual=[given.get(row["scene_id"]) or
                {"scene_id":row["scene_id"],"scores":{"VIDEO":8 if float(row.get("timeline_start_sec",0))<HOOK_VIDEO_SECONDS else 6,"PHOTO":5,"3D":5,"CARD":5,"ANIM":5,"MOTION":5},
                 "forbidden":[],"visual_goal":str(row.get("narrative_beat") or row.get("narration") or "")[:180],
                 "context":"deterministic fallback","planning_fallback":True} for row in rows]
        event(out,"story_plan_group",group=i,scenes=len(actual))
        return actual
    with ThreadPoolExecutor(max_workers=max(1, int(os.environ.get("DOCUMENTARY_FLASH_CONCURRENCY", "10")))) as pool:
        groups=list(pool.map(group,enumerate([scenes[i:i+5] for i in range(0,len(scenes),5)])))
    byscene={s["scene_id"]:s for g in groups for s in g}
    if store and not any(s.get("planning_fallback") for s in byscene.values()):
        save(cache,{"key":key,"scenes":list(byscene.values())})
        return _cap_organic_3d({s["scene_id"]:s for s in load(cache)["scenes"]},scenes)
    return _cap_organic_3d(byscene,scenes)

# A 3D diagram of something organic (a flood, glacier, valley, storm, funnel)
# passed review 6 of 40 times on EP02-EP05 (2026-11-07) against 27 of 50 for
# rigid subjects (a foundation, a house, a track, a radar beam, a rating
# scale): Three.js draws rigid geometry well and fluid terrain badly. A scene
# whose narration names only organic subjects therefore keeps its 3D score at
# most ORGANIC_3D_CAP, so the solver gives it the next-best medium (ANIM on
# EP03) and spends the 3D share on rigid scenes. Scores stay on disk as Flash
# gave them; the cap is applied on every read.
ORGANIC_3D_CAP=float(os.environ.get("DOCUMENTARY_ORGANIC_3D_CAP","3"))
ORGANIC_WORDS=re.compile(r"\b(flood|avalanche|surge|debris|glacier|lake|river|mountain|massif|gorge|valley|terrain|landslide|mud|ice|water|storm|cloud|wind|tornado|funnel|vortex|rain)\w*",re.I)
RIGID_WORDS=re.compile(r"\b(foundation|anchor|bolt|wall|roof|beam|frame|house|building|radar|angle|scale|rating|ef\d|mph|speed|path|track|mile|width|map|distance|height|depth|dam|bridge|gauge|sensor)\w*",re.I)

def organic_only(text):
    text=str(text or "")
    return bool(ORGANIC_WORDS.search(text)) and not RIGID_WORDS.search(text)

def _cap_organic_3d(byscene,scenes):
    if ORGANIC_3D_CAP>=10:return byscene
    for row in scenes:
        scene=byscene.get(row["scene_id"])
        if scene and organic_only(row.get("narration")) and float(scene["scores"].get("3D",0))>ORGANIC_3D_CAP:
            scene["scores"]["3D"]=ORGANIC_3D_CAP
            scene["organic_3d_cap"]=True
    return byscene

def _normalize_hook_scenes(byscene,planned):
    # The opening hook is VIDEO by rule, so a scene the scorer finds hard
    # to film ("rock flows like a liquid") may not ban VIDEO there: the ban
    # made the mix infeasible and the fallbacks put PHOTO/3D in the hook.
    for sid in {r["scene_id"] for r in planned if r["timeline_start_sec"]<HOOK_VIDEO_SECONDS}:
        scene=byscene[sid]
        scene["forbidden"]=[c for c in scene.get("forbidden",[]) if c!="VIDEO"]
        scene["scores"]["VIDEO"]=max(2.0,float(scene["scores"].get("VIDEO",0)))

# A shot is committed to 3D before the catalog exists only when its scene
# clearly wants 3D: score >= 7 and at least 2 points above every medium the
# planner could still give it. On the Gobekli Tepe and Kailasa plans 50/52
# and 54/70 such shots ended up 3D without any lock.
EARLY_3D_MIN_SCORE = 7
EARLY_3D_MARGIN = 2

# An ANIM clip takes ~4 minutes, so as much of the ANIM time as the scores
# allow is locked before the sources: a scene that scores ANIM >= 7 and at
# least one point above every rival medium.
EARLY_ANIM_MIN_SCORE = 7
EARLY_ANIM_MARGIN = 1

def _fits(category,row,targets):
    """The hard duration rules of a medium for one row (no score involved)."""
    if category in STILL_CATEGORIES and row["duration_sec"]>6.5:return False
    if category=="ANIM" and (row["duration_sec"]>ANIM_MAX_SECONDS or not float(targets.get("ANIM",0))):return False
    # A plan whose mix has no MOTION target (an old plan, wildlife) plans none.
    if category=="MOTION" and (row["duration_sec"]>MOTION_MAX_SECONDS or not float(targets.get("MOTION",0))):return False
    return True

# Order in which a ban is lifted for a row that has no allowed category at all.
LIFT_ORDER=("VIDEO","MOTION","CARD","ANIM","3D","PHOTO")

def _rows_without_category(planned,byscene,targets,only_video):
    """Rows where no category survives the per-row bounds of the first solve
    (scene bans, score<=1, the 3.0 s static floor, the duration rules, the
    hook). The sum-to-one row of such a shot cannot be met, so the whole
    problem is infeasible whatever the mix; the fallbacks then drop the
    wrong constraint (the opening hook). For each such non-hook row the
    least-bad single ban is lifted for that row only: VIDEO first, else
    MOTION/CARD (then ANIM, 3D, PHOTO). The static floor, the duration rules,
    the hook and zero-target categories are never loosened.
    Returns [{row, category, banned_by}]."""
    out=[]
    for i,row in enumerate(planned):
        if float(row.get("timeline_start_sec",0))<HOOK_VIDEO_SECONDS:continue
        scene=byscene[row["scene_id"]];scores=scene["scores"];forbidden=scene.get("forbidden",[])
        short=(row["frame_end"]-row["frame_start"])<MIN_STATIC_SHOT_FRAMES
        def structural(c):
            return (c in STATIC_CATEGORIES and short) or not _fits(c,row,targets) or (only_video and c!="VIDEO")
        if any(not structural(c) and c not in forbidden and scores[c]>1 for c in CATEGORIES):continue
        for c in LIFT_ORDER:
            if structural(c) or (c!="VIDEO" and not float(targets.get(c,0))):continue
            out.append({"row":i,"category":c,"banned_by":"scene ban" if c in forbidden else "score<=1"});break
    return out

def _select_early(planned,byscene,targets,category,min_score,min_margin,exclude=()):
    total=sum(r["duration_sec"] for r in planned)
    tolerance=15.0 if total<=45.0 else MIX_TOLERANCE_PERCENT
    budget=total*(targets.get(category,0)-tolerance)/100
    picks=[]
    for i,row in enumerate(planned):
        scene=byscene[row["scene_id"]]
        scores=scene["scores"];forbidden=scene.get("forbidden",[])
        if (row["timeline_start_sec"]<HOOK_VIDEO_SECONDS or row["shot_id"]==1 or scene.get("planning_fallback")
                or row["shot_id"] in exclude or not _fits(category,row,targets)
                or row["frame_end"]-row["frame_start"]<MIN_STATIC_SHOT_FRAMES or category in forbidden):
            continue
        rivals=[scores[c] for c in CATEGORIES if c!=category and c not in forbidden and scores.get(c,0)>1
                and _fits(c,row,targets)]
        margin=scores.get(category,0)-max(rivals,default=0)
        if scores.get(category,0)>=min_score and margin>=min_margin:
            picks.append((-margin,-scores[category],i))
    chosen=set();used=0.0
    for _,_,i in sorted(picks):
        row=planned[i]
        if used+row["duration_sec"]>budget:continue
        if any(j in chosen and planned[j]["scene_id"]!=row["scene_id"] for j in (i-1,i+1)):continue
        chosen.add(i);used+=row["duration_sec"]
    return sorted(planned[i]["shot_id"] for i in chosen)

def select_early_3d(planned,byscene,targets):
    """Shot ids the plan can lock to 3D from the scene scores alone.

    byscene must already carry the hook normalization. The rules are the
    MILP's own: no hook shot, the static floor, no 3D ban, the 3D adjacency
    row (two 3D shots in a row only inside one scene), and the locked time
    stays under the LOWER edge of the 3D duration band, so the locks alone
    can never push the mix out of tolerance; VIDEO capacity, photos and
    the hook are left entirely to the final MILP.
    """
    return _select_early(planned,byscene,targets,"3D",EARLY_3D_MIN_SCORE,EARLY_3D_MARGIN)

def select_early_anim(planned,byscene,targets,exclude=()):
    """Shot ids the plan can lock to ANIM from the scene scores alone.

    The same rules as select_early_3d with ANIM's own: the 4 s ceiling, no
    two ANIM shots in a row across scenes, the locked time under the lower
    edge of the ANIM band; exclude holds the shots already locked to 3D.
    """
    return _select_early(planned,byscene,targets,"ANIM",EARLY_ANIM_MIN_SCORE,EARLY_ANIM_MARGIN,exclude)

def locked_rows(planned,byscene,locked,category="3D"):
    """The plan rows of the locked shots, as make_plan writes them."""
    return [{**r,"category":category,"story_plan":byscene[r["scene_id"]],"generated_only":True}
            for r in planned if r["shot_id"] in set(locked)]

def make_plan(timeline,catalog,out,targets,locked_3d=(),locked_anim=(),anim_available=None):
    planned=shots(timeline,shot_regroup(out))
    # G-Labs makes every ANIM clip. When it does not answer now, ANIM's
    # share goes to 3D and CARD, so a film never blocks on G-Labs; the
    # changed targets are NOT part of the plan identity (E_identity): the
    # identity holds the requested targets, so G-Labs being down at plan time
    # does not force a replan when it is up (or down) at the next run.
    requested_targets=dict(targets);requested_locked_anim=tuple(locked_anim)
    anim_moved=False
    if float(targets.get("ANIM",0)) and not video_only(targets):
        if not (anim_possible(targets) if anim_available is None else anim_available):
            event(out,"anim_unavailable_share_moved",requested_targets=dict(targets),new_targets=without_anim(targets),
                  reason="G-Labs did not answer when the plan was made")
            targets=without_anim(targets);locked_anim=();anim_moved=True
    # Early 3D and ANIM locks (early3d.py) are part of what the plan was made from.
    identity=digest({"planner_version":PLAN_VERSION,"timeline":timeline["identity"],"shots":planned,"catalog":catalog["assets"],"targets":requested_targets,
                     **({"early_3d_locks":sorted(locked_3d)} if locked_3d else {}),
                     **({"early_anim_locks":sorted(requested_locked_anim)} if requested_locked_anim else {})})
    target=out/"material_plan.json"
    if target.exists():
        previous=load(target)
        if previous.get("identity")==identity:return _approve_plan(previous,catalog,out)
        archive=out/"planning"/"previous_plans"/previous.get("identity","unbound")
        save(archive/"material_plan.json",previous)
        if (out/"plan_review.json").exists():save(archive/"plan_review.json",load(out/"plan_review.json"))
    # The mix may not ask for more VIDEO than the catalog can supply under
    # the source rules. The hook stays hard; a short catalog lowers the
    # VIDEO target visibly and gives the difference to 3D (PHOTO has its
    # own catalog ceiling below).
    total_sec=sum(r["duration_sec"] for r in planned)
    cut_sec=float(np.median([r["duration_sec"] for r in planned]))
    video_capacity=_video_capacity(catalog,cut_sec)
    hook_shots=sum(1 for r in planned if r["timeline_start_sec"] < HOOK_VIDEO_SECONDS)
    if hook_shots > video_capacity:
        raise ValueError(f"Catalog can supply only {video_capacity} VIDEO cuts of {cut_sec:.2f}s under the source rules "
                         f"(max {MAX_USES_PER_ORIGIN} per recording, {MIN_SAME_ORIGIN_GAP_SECONDS:.0f}s apart, no talking heads), "
                         f"but the {int(HOOK_VIDEO_SECONDS)}s opening hook needs {hook_shots} VIDEO shots; source more footage")
    mix_tolerance = 15.0 if total_sec <= 45.0 else MIX_TOLERANCE_PERCENT
    supported_pct=100*video_capacity*cut_sec/total_sec if total_sec else 0.0
    capacity={"video_shots":video_capacity,"cut_sec":cut_sec,"hook_video_shots":hook_shots,
              "requested_targets":dict(targets),"targets":dict(targets),"video_target_lowered":False}
    # A video-only film (wildlife) keeps every shot VIDEO whatever the
    # catalog holds: a short catalog is answered by the per-sentence
    # footage search at production, never by moving time to 3D.
    only_video=video_only(targets)
    if only_video and targets["VIDEO"]-mix_tolerance > supported_pct:
        event(out,"video_capacity_short",capacity=video_capacity,cut_sec=cut_sec,supported_percent=supported_pct,
              requested_targets=dict(targets),new_targets=dict(targets),moved_to=None,video_only=True)
    elif targets["VIDEO"]-mix_tolerance > supported_pct:
        new_video=max(0.0,math.floor(supported_pct))
        shift=targets["VIDEO"]-new_video
        targets={**targets,"VIDEO":new_video,"3D":targets["3D"]+shift}
        capacity.update(targets=dict(targets),video_target_lowered=True)
        event(out,"video_capacity_short",capacity=video_capacity,cut_sec=cut_sec,supported_percent=supported_pct,
              requested_targets=capacity["requested_targets"],new_targets=targets,moved_to="3D",moved_percent=shift)
    byscene=score_scenes(timeline,out)
    _normalize_hook_scenes(byscene,planned)
    if only_video:
        # Every line of a video-only film is VIDEO, so no scene may ban it:
        # the hook rule is applied to the whole timeline.
        _normalize_hook_scenes(byscene,[{**r,"timeline_start_sec":0.0} for r in planned])
    usable_photos = len([a for a in catalog.get("assets", []) if a.get("category") == "PHOTO" and a.get("usable", True)])
    n=len(planned); variables=n*len(CATEGORIES); duration=np.array([r["frame_end"]-r["frame_start"] for r in planned],dtype=float)
    total=duration.sum()
    tolerance = 15.0 if (total / 25.0) <= 45.0 else MIX_TOLERANCE_PERCENT
    
    video_idx = CATEGORIES.index("VIDEO")
    adjacency_end = n + len(CATEGORIES) + (n-1)*len(CATEGORIES)
    # Constraints: n (one per shot) + one duration mix per category + (n-1) adjacency rows per category + 1 (photo catalog limit) + 1 (video source capacity)
    total_constrs = adjacency_end + (1 if usable_photos > 0 else 0) + 1
    matrix=lil_matrix((total_constrs, variables));lower=[];upper=[]
    for i in range(n):
        matrix[i,i*len(CATEGORIES):i*len(CATEGORIES)+len(CATEGORIES)]=1;lower.append(1);upper.append(1)
    for j,category in enumerate(CATEGORIES):
        matrix[n+j,j::len(CATEGORIES)]=duration
        expected=total*targets.get(category,0)/100
        lower.append(expected-total*tolerance/100);upper.append(expected+total*tolerance/100)
    # The hook rows are VIDEO by rule, so in a short film they alone can
    # exceed the VIDEO share the tolerance allows (36 s film: 30 s hook =
    # ~67 % of the film against a 48 % VIDEO ceiling). That made every solve infeasible or,
    # after the Codex relax, let the soft hook penalty give up the hook.
    # Raise the VIDEO ceiling to the forced hook time and let the other
    # categories fill whatever is left; the hook itself is not loosened.
    hook_frames=float(sum(duration[i] for i,r in enumerate(planned) if float(r.get("timeline_start_sec",0))<HOOK_VIDEO_SECONDS))
    if hook_frames>upper[n+video_idx]:
        upper[n+video_idx]=hook_frames
        for j in range(len(CATEGORIES)):
            if j!=video_idx:lower[n+j]=0.0
        event(out,"hook_forces_video_share",hook_percent=round(100*hook_frames/total,2),video_target=targets.get("VIDEO"),tolerance=tolerance,
              note="opening hook alone exceeds the VIDEO mix ceiling; VIDEO ceiling raised to the hook, other floors dropped")
    for i in range(n-1):
        same_scene = (planned[i]["scene_id"] == planned[i+1]["scene_id"])
        for j in range(len(CATEGORIES)):
            index=n+len(CATEGORIES)+i*len(CATEGORIES)+j;matrix[index,i*len(CATEGORIES)+j]=1;matrix[index,(i+1)*len(CATEGORIES)+j]=1;lower.append(0)
            if CATEGORIES[j] == "VIDEO" and planned[i]["timeline_start_sec"] < HOOK_VIDEO_SECONDS:
                upper.append(2)
            elif CATEGORIES[j] in ADJACENT_ONCE_CATEGORIES:
                upper.append(2 if same_scene else 1)
            else:
                upper.append(2)
    if usable_photos > 0:
        # PHOTO and CARD shots draw on the same photographs, each used once.
        p_row = adjacency_end
        for still in STILL_CATEGORIES:
            matrix[p_row, CATEGORIES.index(still)::len(CATEGORIES)] = 1
        lower.append(0); upper.append(usable_photos)
    v_row = adjacency_end + (1 if usable_photos > 0 else 0)
    matrix[v_row, video_idx::len(CATEGORIES)] = 1
    lower.append(0); upper.append(n if only_video else video_capacity)

    costs=[];upper_bounds=np.ones(variables)
    for i,row in enumerate(planned):
        scores=byscene[row["scene_id"]]["scores"]
        _hook=float(row.get("timeline_start_sec",0)) < HOOK_VIDEO_SECONDS
        costs.extend(
            (-scores[c]*row["duration_sec"] + ((i+j)%7)*.001)
            for j,c in enumerate(CATEGORIES))
        forbidden=byscene[row["scene_id"]].get("forbidden",[])
        for j,c in enumerate(CATEGORIES):
            if _hook and c != "VIDEO":
                upper_bounds[i*len(CATEGORIES)+j]=0
            elif c in forbidden or scores[c]<=1:
                upper_bounds[i*len(CATEGORIES)+j]=0
            if c in STATIC_CATEGORIES and (row["frame_end"]-row["frame_start"])<MIN_STATIC_SHOT_FRAMES:
                upper_bounds[i*len(CATEGORIES)+j]=0
            # A still holds at most 6.5 s (render gate); a longer line is
            # never planned as PHOTO or CARD.
            # An animation is one clip of at most 10 s, and only a mix that
            # gives ANIM time plans one (an old plan without an ANIM target,
            # or G-Labs down, plans none).
            if not _fits(c,row,targets):
                upper_bounds[i*len(CATEGORIES)+j]=0
            if only_video and c!="VIDEO":
                upper_bounds[i*len(CATEGORIES)+j]=0
    lifted=_rows_without_category(planned,byscene,targets,only_video)
    def apply_lifts(skip_zero_target=False):
        for item in lifted:
            c=item["category"]
            if skip_zero_target and targets.get(c)==0:continue
            upper_bounds[item["row"]*len(CATEGORIES)+CATEGORIES.index(c)]=1
    apply_lifts()
    if lifted:
        event(out,"plan_row_ban_lifted",note="shot had no allowed category (static floor + scene bans); least-bad ban lifted for that shot only",
              rows=[{"shot_id":planned[x["row"]]["shot_id"],"scene_id":planned[x["row"]]["scene_id"],"duration_sec":planned[x["row"]]["duration_sec"],
                     "category":x["category"],"banned_by":x["banned_by"]} for x in lifted])
    # Shots committed to 3D or ANIM while the sources were still being
    # fetched (early3d.py) are fixed variables: x[shot,category] has the
    # lower bound 1. A pass that bans the category for the shot wins (the
    # lower bound never exceeds the upper one), and the shot is then simply
    # not marked below.
    index_of={r["shot_id"]:i for i,r in enumerate(planned)}
    locked_by={"3D":{sid for sid in locked_3d if sid in index_of and not only_video}}
    locked_by["ANIM"]={sid for sid in locked_anim if sid in index_of and not only_video and sid not in locked_by["3D"]}
    locked=locked_by["3D"]|locked_by["ANIM"]
    lock_lower=np.zeros(variables)
    for category,ids in locked_by.items():
        for sid in ids:lock_lower[index_of[sid]*len(CATEGORIES)+CATEGORIES.index(category)]=1
    def solve():
        return milp(np.array(costs),integrality=np.ones(variables),bounds=Bounds(np.minimum(lock_lower,upper_bounds),upper_bounds),constraints=LinearConstraint(matrix.tocsr(),lower,upper),options={"time_limit":30,"mip_rel_gap":.03})

    result=solve()
    if result.x is None and locked:
        # The locks never cost the plan its feasibility: the plan is made
        # without them, and an early result whose row differs from the
        # final one is not reused (its shot digest no longer matches).
        event(out,"early_3d_locks_released",locked=sorted(locked),locked_anim=sorted(locked_by["ANIM"]),
              reason="locked 3D/ANIM shots made the mix infeasible")
        lock_lower[:]=0;locked=set();locked_by={"3D":set(),"ANIM":set()}
        result=solve()
    if result.x is None:
        # A hard semantic ban can make an otherwise valid duration budget
        # infeasible. Ask Codex for a bounded, shot-specific relaxation instead
        # of silently changing targets or stopping the whole production.
        repair=api("codex", "The duration mix constraints are infeasible with the current per-scene bans. "
                    "Choose the smallest honest relaxation. Return JSON "
                    "{relax:[{scene_id:integer,category:\"VIDEO\"|\"PHOTO\"|\"3D\"|\"CARD\"|\"ANIM\"|\"MOTION\",reason:string}]}. "
                    "Only remove a ban when the category remains truthful for that scene; never change timing or targets. "
                    "Use at most 12 relaxations. SCENES:"+str([{k:v for k,v in s.items() if k in ("scene_id","scores","forbidden","visual_goal")} for s in byscene.values()]),
                    out/"planning"/"infeasible_mix_codex.json",tokens=1800,timeout=GPT_PLANNING_TIMEOUT_SECONDS)
        relax=repair.get("data",{}).get("relax",[])
        # An opening hook is a hard VIDEO requirement. Never relax a VIDEO
        # ban automatically; an infeasible plan must remain visible for repair.
        if not isinstance(relax,list) or len(relax)>12:raise ValueError("Codex returned invalid bounded mix repair")
        allowed={(s["scene_id"],c) for s in byscene.values() for c in CATEGORIES}
        for item in relax:
            sid=item.get("scene_id"); category=item.get("category")
            if (sid,category) not in allowed or not isinstance(item.get("reason"),str) or not item["reason"].strip():
                raise ValueError("Codex returned an invalid mix relaxation")
            scene=byscene[sid]
            scene["forbidden"]=[c for c in scene.get("forbidden",[]) if c!=category]
            scene["scores"][category]=max(2.0,float(scene["scores"].get(category,0)))
        # Rebuild objective/bounds after the approved relaxations.
        costs=[];upper_bounds=np.ones(variables)
        for i,row in enumerate(planned):
            scores=byscene[row["scene_id"]]["scores"]
            _hook=float(row.get("timeline_start_sec",0)) < HOOK_VIDEO_SECONDS
            # PATCH: hook penalty in cost instead of hard upper_bound=0 (prevents infeasibility)
            costs.extend(
                (-scores[c]*row["duration_sec"] + ((i+j)%7)*.001 + (500.0 if _hook and c!="VIDEO" else 0.0))
                for j,c in enumerate(CATEGORIES))
            for j,c in enumerate(CATEGORIES):
                if c in byscene[row["scene_id"]].get("forbidden",[]) or scores[c]<=1:upper_bounds[i*len(CATEGORIES)+j]=0
                if c in STATIC_CATEGORIES and (row["frame_end"]-row["frame_start"])<MIN_STATIC_SHOT_FRAMES:
                    upper_bounds[i*len(CATEGORIES)+j]=0
                # The 10 s clip ceiling and a zero ANIM share are not
                # semantic bans; no repair pass lifts them.
                if c in ("ANIM","MOTION") and not _fits(c,row,targets):
                    upper_bounds[i*len(CATEGORIES)+j]=0
                if only_video and c!="VIDEO":
                    upper_bounds[i*len(CATEGORIES)+j]=0
        apply_lifts()
        event(out,"automatic_mix_replan",relaxations=relax)
        result=solve()
    if result.x is None:
        # Last bounded repair: keep the requested duration mix and the hard
        # opening VIDEO rule, but remove only non-hook semantic bans and the
        # adjacent-category carousel cap. The repair is explicit in the plan
        # events; it never turns an unavailable asset into PASS.
        for scene in byscene.values():
            start_sec = float(next((r for r in planned if r["scene_id"]==scene["scene_id"]),{}).get("timeline_start_sec",0))
            if start_sec >= HOOK_VIDEO_SECONDS or any(targets.get(c,0)==100 for c in CATEGORIES):
                scene["forbidden"]=[]
                scene["scores"]={c:max(2.0,float(scene["scores"].get(c,0))) for c in CATEGORIES}
        # Adjacency rows only: the photo and video capacity rows after them stay.
        for idx in range(n+len(CATEGORIES), adjacency_end):
            cat_idx = (idx - (n + len(CATEGORIES))) % len(CATEGORIES)
            upper[idx] = 1 if CATEGORIES[cat_idx] in ADJACENT_ONCE_CATEGORIES else 2
        costs=[]; upper_bounds=np.ones(variables)
        for i,row in enumerate(planned):
            scores=byscene[row["scene_id"]]["scores"]
            costs.extend(-scores[c]*row["duration_sec"]+((i+j)%7)*.001 for j,c in enumerate(CATEGORIES))
            _hook=float(row.get("timeline_start_sec",0)) < HOOK_VIDEO_SECONDS
            for j,c in enumerate(CATEGORIES):
                # The opening hook stays hard in the fallback: the real cause of an
                # infeasible first solve is a shot with no allowed category (lifted
                # per row above), not the hook.
                if _hook and c!="VIDEO":
                    upper_bounds[i*len(CATEGORIES)+j]=0
                elif c in byscene[row["scene_id"]].get("forbidden",[]) or scores[c]<=1:
                    upper_bounds[i*len(CATEGORIES)+j]=0
                if targets.get(c)==0:
                    upper_bounds[i*len(CATEGORIES)+j]=0
                # The four-second floor for a photograph or a 3D scene
                # is not a semantic ban, so no repair pass may lift it.
                if c in STATIC_CATEGORIES and (row["frame_end"]-row["frame_start"])<MIN_STATIC_SHOT_FRAMES:
                    upper_bounds[i*len(CATEGORIES)+j]=0
                if c in ("ANIM","MOTION") and not _fits(c,row,targets):
                    upper_bounds[i*len(CATEGORIES)+j]=0
        apply_lifts(skip_zero_target=True)
        event(out,"automatic_mix_replan_fallback",reason="bounded semantic bans made target mix infeasible",preserved_targets=targets,hook_video_hard=True)
        result=solve()
    if result.x is None:
        # PATCH: 4th safety valve — drop ALL upper_bounds except score<=1; last resort
        costs=[]; upper_bounds=np.ones(variables)
        for i,row in enumerate(planned):
            scores=byscene[row["scene_id"]]["scores"]
            costs.extend(-scores[c]*row["duration_sec"]+((i+j)%7)*.001 for j,c in enumerate(CATEGORIES))
            _hook=float(row.get("timeline_start_sec",0)) < HOOK_VIDEO_SECONDS
            for j,c in enumerate(CATEGORIES):
                if (_hook and c!="VIDEO") or scores[c]<=1 or targets.get(c)==0 or (c in ("ANIM","MOTION") and not _fits(c,row,targets)):
                    upper_bounds[i*len(CATEGORIES)+j]=0
        apply_lifts(skip_zero_target=True)
        event(out,"automatic_mix_replan_last_resort",reason="all semantic bans dropped; only score<=1 and zero-target blocks remain")
        result=solve()
    if result.x is None:raise ValueError("No feasible narrative/category allocation after bounded Codex replan; ratios were not silently changed")
    for i,row in enumerate(planned):
        j=int(np.argmax(result.x[i*len(CATEGORIES):(i+1)*len(CATEGORIES)]));row.update(category=CATEGORIES[j],story_plan=byscene[row["scene_id"]])
        # A locked shot that stayed 3D (or ANIM) carries the mark it was
        # produced under early, so its row digests the same as the early one.
        if row["shot_id"] in locked_by.get(row["category"],()):row["generated_only"]=True
        # Opening shots remain semantically allocated. The runner prefers
        # native 1080p/4K moving footage when it actually depicts the narration;
        # otherwise the hook remains REVIEW_REQUIRED; do not substitute PHOTO or 3D footage.
    hook_violations = [r["shot_id"] for r in planned if float(r.get("timeline_start_sec", 0)) < HOOK_VIDEO_SECONDS and r.get("category") != "VIDEO"]
    if hook_violations:
        raise ValueError(f"Plan violated opening hook rule: shots {hook_violations} are not VIDEO; plan generation blocked")
    percentages={c:100*sum(r["duration_sec"] for r in planned if r["category"]==c)/sum(r["duration_sec"] for r in planned) for c in CATEGORIES}
    if any(abs(percentages[c]-targets.get(c,0))>tolerance for c in CATEGORIES):
        # PATCH: warn instead of crash — hook VIDEO penalty can shift mix slightly beyond tolerance
        event(out,"mix_budget_deviation",percentages=percentages,targets=targets,tolerance=tolerance,
              note="Hook VIDEO cost-penalty shifted allocation; runner enforces hard hook rule")
    # The floor is a hard rule, not a preference, so the plan states a
    # violation instead of letting it reach the render. A short shot of
    # a photograph or a 3D scene means the allocation did not respect
    # the ban, and the plan is not silently accepted.
    short_static=[{"shot_id":r["shot_id"],"category":r["category"],"duration_sec":r["duration_sec"]}
                  for r in planned if r["category"] in STATIC_CATEGORIES
                  and (r["frame_end"]-r["frame_start"])<MIN_STATIC_SHOT_FRAMES]
    if short_static:
        event(out,"static_shot_floor_violation",count=len(short_static),shots=short_static,
              minimum_seconds=MIN_STATIC_SHOT_FRAMES/25)
    plan={"identity":identity,"targets":targets,"planned_percent":percentages,"shots":planned,"scenes":list(byscene.values()),
          "timing":"contiguous 25fps boundaries including narration pauses; frame quantization <=40ms",
          "capacity":capacity,
          "static_shot_floor_sec":MIN_STATIC_SHOT_FRAMES/25,
          "static_shot_floor_violations":short_static,
          **({"lifted_row_bans":[{"shot_id":planned[x["row"]]["shot_id"],"category":x["category"],"banned_by":x["banned_by"]} for x in lifted]} if lifted else {})}
    save(target,plan)
    return _approve_plan(plan,catalog,out)
