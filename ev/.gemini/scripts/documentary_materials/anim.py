"""Generated vox-style animation shots (ANIM), made through G-Labs Studio.

A shot's sentence becomes one illustrative 2D clip in one of six style
presets (STYLES: paper collage, ink engraving, blueprint, screen print,
isometric diorama, archival cut-out) that share one film palette; the
prompt-writing Flash call picks the style per shot and no two neighbouring
ANIM shots share one. The picture is
made in two steps: Nano Banana draws a still frame, Flash checks the still,
then Omni Flash animates it from that frame (mode start_image). Starting
from a checked still keeps the clip on the sentence and keeps the defects
of a text-to-video run (garbled map labels, melting shapes) out of the
first frame; a defect that appears in the motion is caught by the second
check, where Flash watches the clip itself.

Each check that fails makes that step again, up to ATTEMPTS times; a shot
that never passes raises AnimFailed and the runner treats it like any
failed generated shot.

G-Labs Studio is a desktop app; its webhook API must be started in the
app (Webhook tab). The address and key are in glabs_gateway.json beside
documentary_voice_gateway.json:
    {"base_url": "http://127.0.0.1:8765", "api_key": "..."}
"""
import base64
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time

import requests

from .io import SCRIPTS, api, event, load, save

CONFIG = SCRIPTS / "glabs_gateway.json"

IMAGE_MODEL = "nano_banana_pro"
VIDEO_MODEL = "omni_flash"
# Omni Flash makes 4, 6, 8 or 10 second clips; the shortest one that
# covers the shot is asked for and cut to the shot afterwards.
LENGTHS = (4, 6, 8, 10)
MAX_SECONDS = 10.0
ATTEMPTS = 3
POLL_SECONDS = 5
HEDGE_SECONDS = 300
IMAGE_TIMEOUT_SECONDS = 300
VIDEO_TIMEOUT_SECONDS = 900
CHECK_TIMEOUT_SECONDS = 90
# The clip Flash watches: small enough for one request, sharp enough to
# read a garbled label.
CHECK_WIDTH = 640

NO_TEXT = "Absolutely no text, no letters, no labels, no numbers, no captions and no logos anywhere."
# One film palette across every style, so neighbouring shots differ in
# technique, not in colour.
PALETTE = "Film palette: warm cream and off-white, charcoal black and deep red, nothing else saturated."

# Style presets: what the still looks like (image), how it may move
# (motion), and what the prompt writer picks it for (use).
STYLES = {
    "paper_collage": {
        "use": "the default: people, events, ideas, spread across places",
        "image": "Flat 2D vox-style editorial paper collage on a warm off-white paper texture, crisp cut-out shapes with "
                 "soft paper drop shadows, archival engravings and photographs as cut-outs.",
        "motion": "Keep every shape a flat 2D paper cut-out, with gentle parallax between paper layers."},
    "ink_engraving": {
        "use": "early history, science, discoveries, nature, old books and maps",
        "image": "Fine ink engraving and line drawing on aged cream paper, cross-hatched shading in charcoal black, a few "
                 "deep red ink accents, like a 19th-century book plate.",
        "motion": "It stays a flat ink drawing: one ink line may trace itself along a stroke already in the picture; "
                  "the hatching never crawls."},
    "blueprint": {
        "use": "machines, mechanisms, engines, engineering, inventions, how something works",
        "image": "Technical blueprint drawing: precise charcoal and deep red line work on cream drafting paper with a "
                 "faint grid, cutaway and exploded views, plain dimension lines without any figures.",
        "motion": "The line work stays crisp and flat: one part of the mechanism may turn or slide in place along its "
                  "axis."},
    "screen_print": {
        "use": "industry, war, revolutions, propaganda eras, mass movements, strikes",
        "image": "Retro screen-print poster artwork: bold flat shapes in cream, charcoal black and deep red, slight ink "
                 "misregistration and halftone grain, strong silhouettes on a dramatic diagonal, no lettering at all.",
        "motion": "Shapes stay flat printed colour areas: a slow push in, and at most one large silhouette moves a "
                  "little."},
    "isometric_diorama": {
        "use": "cities, factories, ports, systems, networks, infrastructure, logistics",
        "image": "Isometric miniature diorama: handmade paper-model buildings, machines and tiny figures on a cream "
                 "base, seen from a 30-degree isometric angle, soft studio light, cream, charcoal and deep red.",
        "motion": "The camera drifts slowly over the rigid model; at most one vehicle or part moves along its own "
                  "track."},
    "archival_cutout": {
        "use": "real places, buildings, crowds and eras that photographs recorded",
        "image": "2.5D archival-photo cut-out: black-and-white archival photographs cut into foreground, middle and "
                 "background layers on a cream backdrop, deep red accent shapes, soft paper shadows.",
        "motion": "The photo layers slide past each other in slow 2.5D parallax; the photographs themselves never "
                  "move, morph or come alive."},
}
DEFAULT_STYLE = "paper_collage"
COMMON_MOTION = ("No morphing, no melting, no new objects appearing, nothing pops in, vanishes, floats or drifts, "
                 "small objects stay still, no text. Smooth, slow, deliberate motion.")


def style_text(name):
    """The still's style line: the preset, the film palette, no text."""
    return " ".join((STYLES.get(name, STYLES[DEFAULT_STYLE])["image"], PALETTE, NO_TEXT))


def motion_text(name):
    """The clip's motion rules for a preset."""
    return " ".join((STYLES.get(name, STYLES[DEFAULT_STYLE])["motion"], COMMON_MOTION))


# The paper-collage lines, as before the presets.
STYLE = style_text(DEFAULT_STYLE)
MOTION_STYLE = motion_text(DEFAULT_STYLE)
# Changes whenever a preset or a shared rule changes (prompt cache keys).
STYLE_VERSION = repr((sorted((k, sorted(v.items())) for k, v in STYLES.items()), PALETTE, NO_TEXT, COMMON_MOTION))

DEFECTS = ("any visible text, letters, numbers or labels (all text counts, readable or not); "
           "garbled pseudo-writing; morphing, melting or warping objects; extra or broken limbs, fingers or faces; "
           "objects popping in or out; flicker or strobing; a person talking to camera; a logo or watermark; "
           "a picture that does not show the sentence")


class AnimFailed(RuntimeError):
    pass


def _config():
    cfg = load(CONFIG) or {}
    base = os.environ.get("DOCUMENTARY_GLABS_URL") or cfg.get("base_url") or "http://127.0.0.1:8765"
    key = os.environ.get("DOCUMENTARY_GLABS_KEY") or cfg.get("api_key")
    if not key:
        raise AnimFailed("G-Labs API key missing: %s" % CONFIG)
    return base.rstrip("/"), {"X-API-Key": key}


def available():
    """True when the G-Labs webhook server answers."""
    try:
        base, headers = _config()
    except Exception:
        return False
    # A busy G-Labs answers its health check late: on the Blackout run a
    # 5 s timeout called it down 13 times while it was running 4 tasks.
    for wait in (20, 40):
        try:
            if requests.get(base + "/api/health", headers=headers, timeout=wait).ok:
                return True
        except Exception:
            pass
    return False


class _Slot:
    """Cross-process G-Labs slot: every bridge and chat session on this PC
    shares the same GLABS_SLOTS lock files (the fullrun voice/render/mix
    pattern), so two sessions x ten ANIM workers never put more than three
    tasks on G-Labs at once. Ten in parallel drew UNUSUAL_ACTIVITY; three
    is the account's working cap (SISTEM.md), it is not raised here."""
    DIR = Path(os.environ.get("DOCUMENTARY_SLOT_DIR", r"C:\Users\meteh\Belgesel_Teslim\_slots"))

    def __init__(self, name, n):
        self.paths = [self.DIR / ("%s%d.lock" % (name, i)) for i in range(n)]
        self.local = threading.local()

    def __enter__(self):
        import msvcrt
        self.DIR.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        while True:
            for index, p in enumerate(self.paths):
                f = open(p, "a+b")
                try:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    self.local.f, self.local.index = f, index
                    self.local.waited = round(time.monotonic() - started, 1)
                    return self
                except OSError:
                    f.close()
            time.sleep(2)

    def __exit__(self, *a):
        import msvcrt
        f = self.local.f
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            f.close()


# Up to 15 (user 17 Nov; ramp 11-18: 15 parallel 30/30 ok, 4.8x throughput). Ten was allowed once every account carries its own proxy (user, 6 Nov: 25/25 accounts
# proxied, 10 parallel nano_banana_pro 10/10 ok); without proxies keep the default 3.
GLABS_SLOTS = max(1, min(15, int(os.environ.get("DOCUMENTARY_GLABS_SLOTS", "3") or 3)))
_GLABS = _Slot("glabs", GLABS_SLOTS)


def _run(path, body, timeout, shot_dir=None):
    """Submit one G-Labs task and wait for its files; return the first file's bytes.

    A task still running after HEDGE_SECONDS is submitted once more and the
    first copy to finish wins: in a 10-shot run nine clips took 3-5 minutes
    and one waited 13 minutes on the upstream queue, holding the film.
    The whole task, submit to download, holds one of the GLABS_SLOTS
    cross-process slots (the hedge copy rides on the same slot).
    """
    with _GLABS:
        if shot_dir is not None:
            event(shot_dir, "glabs_slot", path=path, slot=_GLABS.local.index, waited_seconds=_GLABS.local.waited)
        return _run_task(path, body, timeout)


def _run_task(path, body, timeout):
    base, headers = _config()

    def submit():
        r = requests.post(base + path, json=body, headers=headers, timeout=120)
        if r.status_code != 202:
            raise AnimFailed("G-Labs %s refused: %s %s" % (path, r.status_code, r.text[:300]))
        return r.json()["task_id"]

    tasks = [submit()]
    started = time.monotonic()
    errors = []
    while time.monotonic() < started + timeout and tasks:
        for task in list(tasks):
            s = requests.get(base + "/api/status/" + task, headers=headers, timeout=30).json()
            if s.get("status") == "completed" and s.get("results"):
                return requests.get(s["results"][-1], timeout=300).content
            if s.get("status") == "failed":
                tasks.remove(task)
                errors.append("%s: %s" % (task, s.get("error_detail") or s.get("error")))
        if len(tasks) == 1 and not errors and time.monotonic() - started > HEDGE_SECONDS:
            tasks.append(submit())
            errors.append(None)  # hedge sent; never send a third
        time.sleep(POLL_SECONDS)
    errors = [e for e in errors if e]
    raise AnimFailed("G-Labs %s: %s" % (path, "; ".join(errors) or "did not finish in %ss" % timeout))


# Candidates drawn at once (DOCUMENTARY_ANIM_RACE; 1 = one at a time as before).
# Measured 2026-11-07 (pre_1107b, 50 ANIM shots): a clip takes 112 s median on
# G-Labs and the slot wait median was 0 s, but 22/50 shots failed the check at
# least once (38 clip and 28 still rejects) and each retry ran serially, so
# anim_make reached 400-800 s. Two candidates per round, first one that passes
# the same check wins; 2 rounds x 2 = 4 candidates at most (was 3 in a row).
RACE = max(1, min(3, int(os.environ.get("DOCUMENTARY_ANIM_RACE", "2") or 2)))


def _rounds():
    return ATTEMPTS if RACE == 1 else max(1, (ATTEMPTS + RACE) // RACE)


def _race(indices, produce, judge):
    """Produce the candidates of one round in parallel and judge each as it lands.

    Returns (path, verdict) of the first that passes, else (None, the last
    verdict). A candidate that raises counts as failed; when every candidate
    raised, the first error is raised. Candidates still running after a pass
    finish in the background (their files stay as attempts).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from . import control
    indices = list(indices)
    if len(indices) == 1:
        attempt = indices[0]
        path = produce(attempt)
        ok, verdict = judge(attempt, path)
        return (path if ok else None), verdict
    ctx = getattr(control._local, "out", None)

    def one(attempt):
        if ctx is not None:
            control._local.out = ctx
        path = produce(attempt)
        return attempt, path, judge(attempt, path)

    pool = ThreadPoolExecutor(max_workers=len(indices), thread_name_prefix="animrace")
    futures = [pool.submit(one, i) for i in indices]
    errors, verdict = [], {}
    try:
        for fut in as_completed(futures):
            try:
                attempt, path, (ok, v) = fut.result()
            except Exception as exc:
                errors.append(exc)
                continue
            verdict = v
            if ok:
                return path, v
        if len(errors) == len(futures):
            raise errors[0]
        return None, verdict
    finally:
        pool.shutdown(wait=False)


def length_for(seconds):
    return next((n for n in LENGTHS if n >= seconds), LENGTHS[-1])


def _check(kind, sentence, receipt, *, images=(), urls=()):
    prompt = (
        "You are the quality gate for one generated %s in a history documentary. Narration sentence: %r. "
        "Look for these defects: %s. A tiny defect that a viewer would not notice at normal speed is not a defect. "
        'Return JSON {"pass": true|false, "fits_sentence": true|false, "defects": [{"at_sec": number|null, '
        '"kind": string, "detail": string}], "fix": "one sentence telling the generator what to change"}.'
        % (kind, sentence, DEFECTS))
    data = api("flash", prompt, receipt, images=images, urls=urls, tokens=1500,
               timeout=CHECK_TIMEOUT_SECONDS, deadline=time.monotonic() + 2 * CHECK_TIMEOUT_SECONDS)["data"]
    ok = bool(data.get("pass")) and bool(data.get("fits_sentence", True)) and not data.get("defects")
    return ok, data


def check_image(path, sentence, receipt):
    return _check("still frame", sentence, receipt, images=(str(path),))


def check_video(path, sentence, receipt):
    with tempfile.TemporaryDirectory() as tmp:
        small = Path(tmp) / "check.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", "scale=%d:-2" % CHECK_WIDTH,
                       "-an", "-c:v", "libx264", "-crf", "30", str(small)], check=True, timeout=120)
        url = "data:video/mp4;base64," + base64.b64encode(small.read_bytes()).decode()
    return _check("video clip", sentence, receipt, urls=(url,))


# 1106 round 2: the still checker fails any visible text or scale mark, so the
# prompt writer must not pick objects that carry them by nature (4 live films:
# 33 of 54 failed still checks were text/marks; EP04 shot 0157 "surveyor
# tripod with measuring rod" failed 3/3 on "graduation marks and numbers").
# The checker (DEFECTS, pass rule) is untouched.
OBJECT_EXAMPLES = "(people, buildings, tools, machines, ships, arrows and lines as plain shapes)"
AVOID_MARKED = (
    "Never name an object that inherently carries text, digits or scale marks, even if you say it has none: "
    "rulers, measuring rods, staffs or tapes, gauges, dials, clocks, meters, thermometers, scales, instrument panels, "
    "maps, charts, graphs, grids with labels, documents, clipboards, forms, screens, monitors, signs, newspapers, "
    "tickets, license plates, scoreboards, magnifier-over-paper scenes. Draw the idea with markless solid shapes "
    "instead (plain blocks, silhouettes, circles, arrows, wavy lines, houses, trees, vehicles, funnels, terrain outlines). ")
# Part of the prompt cache key (runner._anim_prompts keys on STYLE_VERSION): prompts written under the
# old instruction are not reused.
PROMPT_RULES_VERSION = 2
STYLE_VERSION = repr((STYLE_VERSION, PROMPT_RULES_VERSION, OBJECT_EXAMPLES, AVOID_MARKED))

# All locked shots of a film (~15-25) fit one Flash call.
PROMPT_GROUP = 40
PROMPT_TIMEOUT_SECONDS = 60


def topic(timeline):
    """The film topic the prompts are written for, from the timeline alone,
    so the early pool and the main run write the same prompts."""
    named = timeline.get("title") or timeline.get("topic")
    if named:
        return str(named)[:300]
    beats = [str(s.get("narrative_beat") or "") for s in timeline.get("scenes", [])[:8]]
    return " / ".join(b for b in beats if b)[:400]


def _fallback_prompts(row):
    sentence = str(row.get("narration") or "")[:300]
    return {"image_prompt": "Concrete objects that show: " + sentence,
            "motion_prompt": "A slow camera push; the objects stay where they are, with gentle depth between their layers.",
            "source": "fallback"}


def spread_styles(rows, chosen, fixed=None):
    """{shot_id: style} with no two neighbouring ANIM shots in one style.

    rows are the ANIM shots in film order (each one's neighbours are the
    rows before and after it); chosen holds the preferred style per shot,
    fixed the styles already used by neighbours outside this batch
    ({shot_id: set}). A clash takes the next preset in STYLES order.
    """
    fixed = fixed or {}
    names = list(STYLES)
    out, previous = {}, None
    for k, row in enumerate(rows):
        sid = row["shot_id"]
        banned = set(fixed.get(sid, ())) | ({previous} if previous else set())
        want = chosen.get(sid) if chosen.get(sid) in STYLES else DEFAULT_STYLE
        if want in banned:
            start = names.index(want)
            want = next(names[(start + i) % len(names)] for i in range(1, len(names) + 1)
                        if names[(start + i) % len(names)] not in banned)
        out[sid] = previous = want
    return out


def write_prompts(rows, film_topic, folder, feedback=None, fixed=None):
    """{shot_id: {image_prompt, motion_prompt, style, source}} for ANIM rows
    (in film order), one Flash call per group of PROMPT_GROUP shots. Flash
    picks each shot's style preset from its sentence; spread_styles then
    keeps neighbouring shots apart (fixed: {shot_id: styles of neighbours
    made outside this batch}). A shot the answer leaves out or answers
    badly gets a plain prompt from its own sentence."""
    from concurrent.futures import ThreadPoolExecutor
    import json

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    menu = "; ".join("%s (%s)" % (name, s["use"]) for name, s in STYLES.items())

    def group(entry):
        index, batch = entry
        prompt = (
            "Write generation prompts for illustrative 2D animation shots of a history documentary. "
            "Film topic: %s. First pick each shot's style from these presets, by what its sentence is about: %s. "
            "Neighbouring shots (consecutive in the list) must not share a style. "
            "For each shot write image_prompt: one still frame (16:9) built from concrete objects drawn in that style "
            "%s "
            "arranged to show the sentence; at most five large objects, no loose sheets of paper, no scattered small "
            "pieces; name every object, its place in the frame and its colour (cream, charcoal black, deep red). "
            "%s"
            "The picture must contain no text at all: no letters, words, numbers, labels, captions, signs, banners with "
            "writing, books or pages. Then motion_prompt: a slow camera push or pan plus at most two motions of large "
            "objects already in the still (a line drawing itself along a path, one object sliding or turning in place); "
            "every other object stays still; nothing appears, disappears, floats or drifts; no morphing, no cuts. "
            "Each prompt at most 70 words; the style itself is added later, so describe the content. "
            'Return JSON {"shots":[{"shot_id":int,"style":string,"image_prompt":string,"motion_prompt":string}]}, every shot_id once. '
            % (film_topic, menu, OBJECT_EXAMPLES, AVOID_MARKED)
            + ("Earlier clips for these shots were rejected; fix this: %s " % json.dumps(feedback, ensure_ascii=False)[:1200]
               if feedback else "")
            + "SHOTS:" + json.dumps([{"shot_id": r["shot_id"], "sentence": r.get("narration"),
                                      "scene": str(r.get("full_scene_narration") or "")[:500]} for r in batch],
                                     ensure_ascii=False))
        receipt = folder / ("p%02d.json" % index)
        try:
            answer = api("flash", prompt, receipt, tokens=300 + 260 * len(batch), timeout=PROMPT_TIMEOUT_SECONDS,
                         deadline=time.monotonic() + 2 * PROMPT_TIMEOUT_SECONDS)["data"].get("shots")
        except Exception as exc:
            answer = []
            event(folder, "anim_prompts_fallback", group=index, shots=len(batch), error=type(exc).__name__)
        given = {}
        for r in answer if isinstance(answer, list) else []:
            if (isinstance(r, dict) and all(isinstance(r.get(k), str) and 10 <= len(r[k].strip()) <= 900
                                            for k in ("image_prompt", "motion_prompt"))):
                given.setdefault(r.get("shot_id"), {"image_prompt": r["image_prompt"].strip(),
                                                    "motion_prompt": r["motion_prompt"].strip(),
                                                    "style": r.get("style"), "source": "flash"})
        return {r["shot_id"]: given.get(r["shot_id"]) or _fallback_prompts(r) for r in batch}

    rows = list(rows)
    groups = [rows[i:i + PROMPT_GROUP] for i in range(0, len(rows), PROMPT_GROUP)]
    if not groups:
        return {}
    with ThreadPoolExecutor(max_workers=min(len(groups), 4)) as pool:
        written = {k: v for answer in pool.map(group, enumerate(groups)) for k, v in answer.items()}
    styles = spread_styles(rows, {sid: p.get("style") for sid, p in written.items()}, fixed)
    for sid, prompts in written.items():
        if prompts.get("style") != styles[sid]:
            prompts["style_requested"] = prompts.get("style")
        prompts["style"] = styles[sid]
    return written


def rewrite_image_prompt(image_prompt, sentence, verdict, receipt, style=DEFAULT_STYLE):
    """A new image prompt for a still the checker rejected: same idea, with the
    checker's defects and fix taken into account and no object that carries
    text or marks by nature. Falls back to the old prompt when Flash fails."""
    import json
    prompt = (
        "A generated still for a history documentary was rejected by its quality gate. Narration sentence: %r. "
        "Style: %s. Rejected image prompt: %r. Gate defects: %s. Gate fix: %s. "
        "Rewrite the image prompt so the same sentence is still shown, but replace every object that caused the "
        "defects. %s%s"
        'Same rules as before: at most five large objects, each with place and colour (cream, charcoal black, deep red), '
        "no text at all, at most 70 words, describe the content only. "
        'Return JSON {"image_prompt": string}.'
        % (sentence, style, image_prompt, json.dumps(verdict.get("defects"), ensure_ascii=False)[:800],
           verdict.get("fix") or "", AVOID_MARKED, ""))
    try:
        got = api("flash", prompt, receipt, tokens=500, timeout=PROMPT_TIMEOUT_SECONDS,
                  deadline=time.monotonic() + 2 * PROMPT_TIMEOUT_SECONDS)["data"].get("image_prompt")
    except Exception:
        return image_prompt
    return got.strip() if isinstance(got, str) and 10 <= len(got.strip()) <= 900 else image_prompt


def make_still(shot_dir, sentence, image_prompt, style=DEFAULT_STYLE):
    """The checked still of a shot: Nano Banana draws it in the style, Flash
    checks it, up to ATTEMPTS times; returns its path or raises AnimFailed.

    A rejected still is never drawn again from the same prompt: the next
    attempt uses a prompt Flash rewrote from the checker's defects and fix
    (still_prompt.json keeps the latest one, so a fresh try of the same shot
    starts from it instead of from the prompt that failed)."""
    shot_dir = Path(shot_dir)
    shot_dir.mkdir(parents=True, exist_ok=True)
    kept = load(shot_dir / "still_prompt.json") if (shot_dir / "still_prompt.json").exists() else {}
    current = kept.get("current") if kept.get("original") == image_prompt and kept.get("current") else image_prompt
    note = ""
    for rnd in range(_rounds()):
        base = rnd * RACE
        prompt = current + " " + style_text(style) + note

        def produce(attempt, prompt=prompt):
            still = shot_dir / ("still_%d.png" % attempt)
            still.write_bytes(_run("/api/image/generate", {"prompt": prompt, "model": IMAGE_MODEL,
                                                           "aspect_ratio": "16:9"}, IMAGE_TIMEOUT_SECONDS))
            return still

        def judge(attempt, still):
            ok, verdict = check_image(still, sentence, shot_dir / ("still_check_%d.json" % attempt))
            event(shot_dir, "anim_still_checked", attempt=attempt, passed=ok, style=style, defects=verdict.get("defects"))
            return ok, verdict

        still, verdict = _race(range(base, base + RACE), produce, judge)
        if still is not None:
            return still
        current = rewrite_image_prompt(current, sentence, verdict, shot_dir / ("still_rewrite_%d.json" % base), style)
        save(shot_dir / "still_prompt.json", {"original": image_prompt, "current": current})
        event(shot_dir, "anim_still_rewritten", attempt=base, prompt=current[:300])
        note = " Fix from the last attempt: %s" % (verdict.get("fix") or "")
    raise AnimFailed("no still passed the check in %d candidates" % (_rounds() * RACE))


def make(shot_dir, sentence, image_prompt, motion_prompt, seconds, style=DEFAULT_STYLE):
    """Make one checked clip for a shot; return its path (raw G-Labs mp4, 1080p).

    shot_dir holds every attempt and every verdict, so a restart reuses a
    clip already accepted for the same prompts and style.
    """
    shot_dir = Path(shot_dir)
    shot_dir.mkdir(parents=True, exist_ok=True)
    style = style if style in STYLES else DEFAULT_STYLE
    length = length_for(seconds)
    record = shot_dir / "anim_result.json"
    key = {"sentence": sentence, "image_prompt": image_prompt, "motion_prompt": motion_prompt, "length": length,
           "image_model": IMAGE_MODEL, "video_model": VIDEO_MODEL, "style": style_text(style),
           "style_name": style, "motion_style": motion_text(style)}
    done = load(record) if record.exists() else {}
    if done.get("key") == key and Path(done.get("clip", "")).is_file():
        return Path(done["clip"])

    started = time.monotonic()
    video_note = ""
    still = make_still(shot_dir, sentence, image_prompt, style)

    reference = "data:image/png;base64," + base64.b64encode(still.read_bytes()).decode()
    for rnd in range(_rounds()):
        base = rnd * RACE
        body = {"prompt": motion_prompt + " " + motion_text(style) + video_note, "model": VIDEO_MODEL,
                "mode": "start_image", "aspect_ratio": "16:9", "video_length": length, "resolution": ["1080p"],
                "remove_logo": True, "reference_images": [reference]}

        def produce(attempt, body=body):
            clip = shot_dir / ("clip_%d.mp4" % attempt)
            clip.write_bytes(_run("/api/video/generate", body, VIDEO_TIMEOUT_SECONDS, shot_dir))
            return clip

        def judge(attempt, clip):
            ok, verdict = check_video(clip, sentence, shot_dir / ("clip_check_%d.json" % attempt))
            event(shot_dir, "anim_clip_checked", attempt=attempt, passed=ok, defects=verdict.get("defects"))
            return ok, verdict

        clip, verdict = _race(range(base, base + RACE), produce, judge)
        if clip is not None:
            save(record, {"key": key, "clip": str(clip), "still": str(still), "style": style,
                          "seconds": round(time.monotonic() - started, 1)})
            return clip
        video_note = " Fix from the last attempt: %s" % (verdict.get("fix") or "")
    raise AnimFailed("no clip passed the check in %d candidates" % (_rounds() * RACE))
