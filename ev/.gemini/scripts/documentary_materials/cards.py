"""CARD shots: one real photograph on a white explainer card.

The style is the one the user approved on the whitecard-ibm-pc, -tesla,
-titanic and cs2-buy-guide HyperFrames builds: pure white, the photograph
cut out with a soft drop shadow (pop-in with a slight overshoot, then a
slow 1.00 -> 1.05 push), a maroon banner sliding down, a hand-drawn arrow
drawing on toward the subject, a bold annotation with a black box behind
its key word, an optional count-up, an optional red X for a failure and a
date/stat badge lower left. Every element lands on a narration word, and
nothing moves in the last ~1.5 s.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import numpy as np
from PIL import Image
from scipy import ndimage

from .io import api, event, save

ROOT = Path(__file__).resolve().parent
W, H = 1920, 1080
FPS = 25
# The CLI version the approved builds were rendered with.
HYPERFRAMES = "hyperframes@0.8.181"


def hyperframes_command():
    """The command that runs HyperFrames: the installed copy when it is the approved
    version (npx --yes costs 2.5-12 s per call, the node start 0.2 s), else npx."""
    exe = shutil.which("hyperframes")
    node = shutil.which("node")
    if exe and node:
        root = Path(exe).resolve().parent / "node_modules" / "hyperframes"
        try:
            if json.loads((root / "package.json").read_text(encoding="utf8"))["version"] == HYPERFRAMES.split("@")[1]:
                return [node, str(root / "bin" / "hyperframes.mjs")]
        except (OSError, ValueError, KeyError):
            pass
    return [shutil.which("npx") or "npx", "--yes", HYPERFRAMES]


def render_project(project, raw, count):
    """Render a HyperFrames-style project (index.html + GSAP timeline) to raw at 25 fps.

    Default: fastrender.mjs (one browser, frames piped to ffmpeg; ~2x faster, ~0.7 GB
    instead of 1.7 GB). On any failure, or with DOCUMENTARY_FASTRENDER=0, HyperFrames.
    Callers hold the hyperframes slot.
    """
    node = shutil.which("node")
    if node and os.environ.get("DOCUMENTARY_FASTRENDER", "1") != "0":
        try:
            done = subprocess.run([node, str(ROOT / "fastrender.mjs"), "--frames", str(count), f"{project}::{raw}"],
                                  capture_output=True, text=True, encoding="utf8", errors="replace", timeout=300)
            if not done.returncode and Path(raw).is_file():
                return "fastrender"
            print("fastrender failed, using HyperFrames: " + (done.stderr or done.stdout or "")[-300:], file=__import__("sys").stderr)
        except (OSError, subprocess.SubprocessError) as error:
            print("fastrender failed, using HyperFrames: " + str(error)[:300], file=__import__("sys").stderr)
        Path(raw).unlink(missing_ok=True)
    done = subprocess.run([*hyperframes_command(), "render", str(project), "-o", str(raw), "--fps", str(FPS),
                           "--workers", "1", "--experimental-fast-capture=false", "--quiet"],
                          capture_output=True, text=True, encoding="utf8", errors="replace", timeout=300)
    if done.returncode or not Path(raw).is_file():
        raise RuntimeError("HyperFrames render failed: " + (done.stderr or done.stdout or "")[-800:])
    return "hyperframes"

# Card content is short Flash work: 15 cards per call, the group size the
# shot goals use, under the planning ceiling (planning.PLANNING_TIMEOUT_SECONDS).
CONTENT_GROUP = 15
CONTENT_TIMEOUT_SECONDS = 45

BANNER_MAX_WORDS = 5
NOTE_MAX_WORDS = 6
BADGE_MAX_WORDS = 4

# The last seconds of a card hold still, so the cut out of it is calm.
HOLD_SECONDS = 1.5

# Where the picture may sit: right of the badge (left 80, ~240 wide) and
# under the banner (top 48, ~82 high), leaving the right third for the note.
SUBJECT_BOX = (300, 170, 1140, 960)
NOTE_FONT = 56
# Montserrat 900 runs ~0.68 em per character on the approved cards
# ("about 300" = 9 characters at 56 px measured 330 px plus the box padding).
NOTE_EM_PER_CHAR = 0.68


def _norm(word):
    return re.sub(r"[^0-9a-z]", "", str(word).lower())


def shot_words(timeline, row):
    """The narration words of a shot, in shot-local seconds.

    A word belongs to the shot whose frames hold its midpoint, the rule
    planning.shots cuts the narration with; a shot that runs on over a
    merged neighbour (continues_over) keeps every word under its frames.
    """
    start, end = row["frame_start"] / FPS, row["frame_end"] / FPS
    words = []
    for scene in timeline.get("scenes", []):
        for w in scene.get("word_timestamps", []):
            mid = (float(w["start"]) + float(w["end"])) / 2
            if start <= mid < end:
                words.append({"word": str(w["word"]), "start": round(max(0.0, float(w["start"]) - start), 3),
                              "end": round(max(0.0, float(w["end"]) - start), 3)})
    return words


def subject(asset):
    """The fallback banner: what the photograph shows, in at most five words.

    The classifier's description names the subject after a lead such as
    "A black-and-white photograph of"; the lead and anything after the
    first clause ("..., about 1890", "... with keyboard") are left out.
    """
    for text in (asset.get("subject"), asset.get("description"), asset.get("source_title")):
        text = re.sub(r"^file:|\.(jpe?g|png|webp|tiff?)$", "", str(text or "").strip(), flags=re.I)
        text = re.sub(r"^.{0,60}?\b(photo(graph)?|image|picture|scan|portrait|view)\s+(of|showing)\s+(an?\s+|the\s+)?",
                      "", text, flags=re.I)
        text = re.split(r"[,;:(]|\s(?:with|in|on|at|during|from|showing|wearing|circa|c\.)\s", text, maxsplit=1)[0]
        words = re.findall(r"[\w'’&.-]+", text)
        if words:
            return " ".join(words[:BANNER_MAX_WORDS])
    return "Archive photograph"


def _find(words, target, after=0.0):
    """The local start of the first narration word that matches target."""
    key = _norm(target)
    if not key:
        return None
    for w in words:
        if _norm(w["word"]) == key and w["start"] >= after:
            return w["start"]
    return None


def _digits(text):
    return set(re.findall(r"\d+", str(text).replace(",", "")))


def validate(answer, item):
    """A card's content, checked against the narration it is spoken over.

    Every part that has to land on a word must name a word the narration
    really has, and every figure on the card must be a figure the
    narration or the photograph's own description gives: the card may
    not invent a number. A part that fails is dropped; a missing or
    broken answer leaves the banner (the photograph's subject) alone.
    """
    words = item["words"]
    known = _digits(" ".join(w["word"] for w in words) + " " + str(item.get("description", "")))
    issues = []
    answer = answer if isinstance(answer, dict) else {}
    card = {"banner": subject(item), "note": None, "badge": None, "failure_at": None,
            "source": "fallback" if not answer else "flash"}

    banner = answer.get("banner")
    if isinstance(banner, str) and 1 <= len(banner.split()) <= BANNER_MAX_WORDS and len(banner) <= 42:
        card["banner"] = banner.strip()
    elif answer:
        issues.append("banner")

    note = answer.get("annotation")
    if isinstance(note, str) and note.strip():
        tokens = note.split()
        hl = _norm(answer.get("highlight"))
        index = next((i for i, t in enumerate(tokens) if _norm(t) == hl), None) if hl else None
        at = _find(words, answer.get("annotation_word"))
        if not 1 <= len(tokens) <= NOTE_MAX_WORDS or index is None or at is None or not _digits(note) <= known:
            issues.append("annotation")
        else:
            card["note"] = {"words": tokens, "highlight": index, "at": at}
            number = answer.get("number")
            count_index = next((i for i, t in enumerate(tokens) if isinstance(number, str) and t == number.strip()), None)
            number_at = _find(words, answer.get("number_word"))
            if count_index is not None and _digits(number) and number_at is not None:
                card["note"].update(count_index=count_index, count_at=number_at)
            elif number:
                issues.append("number")

    badge = answer.get("badge")
    if isinstance(badge, str) and badge.strip():
        if 1 <= len(badge.split()) <= BADGE_MAX_WORDS and len(badge) <= 28 and _digits(badge) <= known:
            card["badge"] = {"text": badge.strip(), "at": _find(words, answer.get("badge_word"))}
        else:
            issues.append("badge")

    if answer.get("failure_word"):
        card["failure_at"] = _find(words, answer["failure_word"])
        if card["failure_at"] is None:
            issues.append("failure_word")
    card["issues"] = issues
    return card


def _prompt(group):
    return ('Write the on-screen text of documentary explainer CARDS. A card shows ONE real photograph (described in '
            'subject) on white, a title banner, a short annotation with one highlighted key word and an arrow to the '
            'subject; the viewer hears the narration at the same time. Use only facts the narration states or the '
            'subject description shows; never invent a number, date or name. '
            'banner: at most 5 words naming what the photograph shows (the person, product, object, document or '
            'organisation). annotation: at most 6 words, the fact the narration says about it; highlight: one word of '
            'the annotation, copied exactly. annotation_word: the narration word the annotation should appear on, '
            'copied exactly from the narration. number: optional, a figure the narration states, written exactly as '
            'one word of the annotation (e.g. "1,500+"), with number_word the narration word it lands on. '
            'failure_word: optional, only when the sentence states a failure, loss, ban or death: the narration word '
            'that says it. badge: optional date or statistic of at most 4 words that the narration or the subject '
            'description gives, with badge_word the narration word it lands on, or null. '
            'Return JSON {cards:[{shot_id,banner,annotation,highlight,annotation_word,number,number_word,'
            'failure_word,badge,badge_word}]}, every requested shot_id once; use null for an absent optional field. '
            'CARDS:' + json.dumps([{"shot_id": i["shot_id"], "narration": " ".join(w["word"] for w in i["words"]),
                                    "subject": str(i.get("description", ""))[:240]} for i in group], ensure_ascii=False))


def contents(items, folder):
    """Card content for a batch of CARD shots, one Flash call per group.

    items: [{shot_id, words, description, subject?, source_title?}]. The
    answer is checked per card (validate); a group whose call fails, or a
    card the answer leaves out, keeps the fallback, so a card is never
    lost to its text.
    """
    folder = Path(folder)
    # The shot folder may not exist yet; the fallback event is written there.
    folder.mkdir(parents=True, exist_ok=True)

    def group(entry):
        index, batch = entry
        receipt = folder / f"card_content_{index:02}.json"
        try:
            rows = api("flash", _prompt(batch), receipt, tokens=400 + 260 * len(batch), timeout=CONTENT_TIMEOUT_SECONDS,
                       deadline=time.monotonic() + 2 * CONTENT_TIMEOUT_SECONDS)["data"].get("cards")
        except Exception as exc:
            rows = []
            event(folder, "card_content_fallback", group=index, shots=len(batch), error=type(exc).__name__)
        given = {}
        for r in rows if isinstance(rows, list) else []:
            if isinstance(r, dict):
                given.setdefault(r.get("shot_id"), r)
        return {i["shot_id"]: validate(given.get(i["shot_id"]), i) for i in batch}

    groups = [items[i:i + CONTENT_GROUP] for i in range(0, len(items), CONTENT_GROUP)]
    with ThreadPoolExecutor(max_workers=max(1, min(len(groups), int(os.environ.get("DOCUMENTARY_FLASH_CONCURRENCY", "10"))))) as pool:
        return {k: v for answer in pool.map(group, enumerate(groups)) for k, v in answer.items()}


def _rembg_cutout(image):
    """The u2net general model, when it is installed with its weights.

    Nothing is downloaded: without the local model file this answers None.
    """
    if not (Path.home() / ".u2net" / "u2net.onnx").is_file():
        return None
    try:
        import rembg
        cut = rembg.remove(image, session=rembg.new_session("u2net"))
    except Exception:
        return None
    alpha = np.asarray(cut.getchannel("A"), dtype=np.float32) / 255
    # A matte that keeps (almost) nothing or (almost) everything is a miss.
    return cut if 0.05 <= alpha.mean() <= 0.95 else None


def _white_key(image):
    """Key a plain light background off a photograph, or None.

    The approved IBM PC card was keyed this way after the HyperFrames
    remove-background (a human segmentation model) left a blobby matte on
    the object: near-white pixels connected to the border are background,
    1.2 px feather. A light region the border does not reach (a white
    label on the object) stays. Refused when the border is mostly not
    light (a real scene) or the background is under 8% or over 85% of the
    picture: a page scan's paper is the subject, not its background.
    """
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    light = (rgb.min(axis=2) >= 232) & (rgb.max(axis=2) - rgb.min(axis=2) <= 18)
    border = np.concatenate([light[0], light[-1], light[:, 0], light[:, -1]])
    if border.mean() < 0.7:
        return None
    labels, _ = ndimage.label(light)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    background = np.isin(labels, edge[edge > 0])
    if not 0.08 <= background.mean() <= 0.85:
        return None
    alpha = ndimage.gaussian_filter((~background).astype(np.float32), 1.2)
    cut = image.convert("RGB").copy()
    cut.putalpha(Image.fromarray(np.clip(alpha * 255, 0, 255).astype(np.uint8)))
    return cut


def cutout(source, folder):
    """The card's picture: a cutout PNG, or the photograph as a tilted print.

    Returns (path, mode) with mode "cutout" or "photo". Never raises for a
    picture it cannot cut: the print is the fallback.
    """
    folder = Path(folder)
    with Image.open(source) as img:
        img = img.convert("RGB")
        # 1600 px is above the largest box a card gives a picture (840x790).
        img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        for method in (_rembg_cutout, _white_key):
            cut = method(img)
            if cut is not None:
                box = cut.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
                if box:
                    path = folder / "card_cutout.png"
                    cut.crop(box).save(path)
                    return path, "cutout"
        path = folder / "card_photo.jpg"
        img.save(path, quality=92)
        return path, "photo"


def _tip(path, mode, scale):
    """Where the arrow points, in picture pixels: just off a cutout's
    opaque right edge at a third of its height, or onto a print, 12% in
    from its right edge (the Titanic card points into its page)."""
    with Image.open(path) as img:
        w, h = img.size
        rows = range(int(h * 0.25), int(h * 0.45) + 1)
        if mode == "cutout":
            alpha = np.asarray(img.getchannel("A"))
            best = None
            for y in rows:
                xs = np.nonzero(alpha[y] > 128)[0]
                if xs.size and (best is None or xs[-1] > best[0]):
                    best = (int(xs[-1]), y)
            if best:
                return best[0] * scale + 14, best[1] * scale
        return w * 0.88 * scale, h * 0.32 * scale


def _count_steps(token, start, land):
    """The count-up as (time, text) steps that keep the token's own format."""
    match = re.search(r"\d[\d,]*(\.\d+)?", token)
    prefix, number, suffix = token[:match.start()], match.group(0), token[match.end():]
    value = float(number.replace(",", ""))
    decimals = len(match.group(1)) - 1 if match.group(1) else 0
    steps = max(2, min(15, int((land - start) * FPS)))
    out = []
    for k in range(steps + 1):
        # ease-out: fast at first, settling on the spoken figure
        v = value * (1 - (1 - k / steps) ** 3)
        text = f"{v:,.{decimals}f}" if "," in number else f"{v:.{decimals}f}"
        out.append([round(start + (land - start) * k / steps, 3), prefix + text + suffix])
    return out


def layout(card, picture, mode, count):
    """The template's configuration: positions in pixels, times in seconds."""
    duration = count / FPS
    # A shot is at least 3.0 s (planning.MIN_STATIC_SHOT_FRAMES); a short
    # one keeps a shorter hold so its words still get time to land.
    still = duration - (HOLD_SECONDS if duration >= 4.0 else max(0.6, duration * 0.3))
    with Image.open(picture) as img:
        w, h = img.size
    x0, y0, x1, y1 = SUBJECT_BOX
    scale = min((x1 - x0) / w, (y1 - y0) / h)
    dw, dh = w * scale, h * scale
    left, top = (x0 + x1) / 2 - dw / 2, (y0 + y1) / 2 - dh / 2
    tip_x, tip_y = _tip(picture, mode, scale)
    config = {"banner": card["banner"],
              "t": {"banner": 0.05, "subject": 0.0, "still": round(still, 3), "duration": round(duration, 3)},
              "subject": {"left": round(left, 1), "top": round(top, 1), "width": round(dw, 1), "height": round(dh, 1),
                          "origin": [round(tip_x - 14, 1), round(tip_y, 1)]},
              "note": None, "arrow": None, "stamp": None, "badge": None}

    def clamp(at, lo, hi):
        return round(min(max(lo, at if at is not None else lo), max(lo, hi)), 3)

    note = card.get("note")
    if note:
        words = note["words"]
        lines = [list(range(len(words)))] if len(words) <= 3 else [list(range(math.ceil(len(words) / 2))),
                                                                     list(range(math.ceil(len(words) / 2), len(words)))]
        tx, ty = left + tip_x, top + tip_y
        # The approved arrows run ~200 px and rise ~90 px from the note's
        # first line to the subject; a note right against a narrow picture
        # left a 60 px squiggle, so the note keeps that distance from the tip.
        note_left = min(max(tx + 220, left + dw + 60), 1240)
        widest = max(sum(len(words[i]) + 1 for i in line) + (1 if note["highlight"] in line else 0) for line in lines)
        size = min(NOTE_FONT, int((W - 40 - note_left) / (NOTE_EM_PER_CHAR * widest)))
        note_top = clamp(ty + 90 - size * 0.62, 280, 700)
        span = 0.11 * len(words) + 0.3 + 0.15
        at = clamp(note["at"] - 0.1, 0.5, still - span - 0.64)
        config["note"] = {"words": words, "lines": lines, "highlight": note["highlight"], "left": round(note_left, 1),
                          "top": note_top, "size": size, "at": at, "count_index": None, "count": None}
        if note.get("count_index") is not None:
            # the figure counts up while its word is spoken and lands on it
            land = clamp(note["count_at"], at + 0.4, still)
            config["note"].update(count_index=note["count_index"],
                                  count=_count_steps(words[note["count_index"]], max(at + 0.1, land - 0.6), land))
        sx, sy = note_left - 20, note_top + size * 0.62
        dx = sx - tx
        # out level from the note, then up into the subject (the approved swoop)
        config["arrow"] = {"at": clamp(at + span, at, still - 0.64),
                           "d": "M %.1f %.1f C %.1f %.1f, %.1f %.1f, %.1f %.1f" % (sx, sy, sx - 0.4 * dx, sy + 10,
                                                                                tx + 0.2 * dx, ty + 0.55 * (sy - ty), tx, ty)}
    if card.get("failure_at") is not None:
        config["stamp"] = {"left": round(left + dw * 0.15 - 65, 1), "top": round(top + dh * 0.6 - 65, 1),
                           "at": clamp(card["failure_at"], 0.6, still - 0.4)}
    if card.get("badge"):
        config["badge"] = {"text": card["badge"]["text"], "at": clamp(card["badge"]["at"] or 0.7, 0.4, still - 0.35)}
    return config


def write_project(card, picture, mode, count, work):
    """A HyperFrames project for one card: the template with its values in."""
    project = Path(work) / "card_project"
    for sub in ("vendor", "assets"):
        (project / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "three_vendor" / "gsap.min.js", project / "vendor" / "gsap.min.js")
    shutil.copy2(picture, project / "assets" / Path(picture).name)
    config = layout(card, picture, mode, count)
    source = (ROOT / "card_template.html").read_text(encoding="utf8")
    title = re.sub(r"[<>&\"]", "", card["banner"])
    source = (source.replace("__TITLE__", title).replace("__DURATION__", str(config["t"]["duration"]))
              .replace("__MODE__", mode).replace("__SRC__", "assets/" + Path(picture).name)
              .replace("__CONFIG__", json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")))
    (project / "index.html").write_text(source, encoding="utf8")
    save(project / "hyperframes.json", {"paths": {"assets": "assets"}})
    save(project / "card_config.json", config)
    return project


def render_card(asset, count, output, work):
    """Render one CARD shot to output at exactly count frames of 25 fps.

    HyperFrames renders the card (it embeds Montserrat); the file is then
    encoded once more with the pipeline's own encoder, so the clip joins
    the stream-copy concat (runner._concat) like every other shot.
    """
    from .three_render import _governor, encoding_slot
    from .io import run
    if type(count) is not int or count <= 0:
        raise ValueError("A card needs a positive frame count")
    work = Path(work)
    picture, mode = cutout(asset["path"], work)
    project = write_project(asset["card"], picture, mode, count, work)
    raw = work / "card_raw.mp4"
    # Measured on a 150-frame card on this machine: the default capture
    # (drawElementImage on the hardware GPU) took 82.3 s, screenshot capture
    # 15.8 s with one browser, 11.3 s with four. Cards render side by side
    # under the hyperframes slot, so each takes one browser and screenshots.
    with _governor().slot("hyperframes"):
        render_project(project, raw, count)
    with encoding_slot() as encoder:
        run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vf", "fps=25,setsar=1,tpad=stop_mode=clone:stop_duration=1",
             "-frames:v", count, "-an", *encoder, "-pix_fmt", "yuv420p", "-movflags", "+faststart", output], 180)
    save(work / "card_receipt.json", {"mode": mode, "picture": str(picture), "project": str(project), "frame_count": count})
    return mode
