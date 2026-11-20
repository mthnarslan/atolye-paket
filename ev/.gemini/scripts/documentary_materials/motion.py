"""MOTION shots: code-drawn motion graphics made from the shot's sentence.

The style is the one the user approved on the ml1_orbital and
ml2_dashboard HyperFrames builds (Matt Loui's code-driven look): a dark
navy space with rings and glowing tracks, or a light keynote board with
white cards, drawn connectors and a travelling pulse. Five layouts:

    kinetic   2-3 power words snap in, then a number or year counts up
    timeline  dated cards with connectors and a pulse
    stat      a metric card: count-up, bars and a pill
    route     named places as nodes joined by drawn links (no map image)
    process   numbered steps with a filling progress track

One batched Flash call turns each shot's narration into a layout and its
words; every number, year, name and place on screen has to come from the
shot's own narration (validate drops the rest and falls back to kinetic
words taken from the sentence). Each item lands on the narration word
that says it (Whisper times), and the last ~1 s keeps a slow idle motion.
Neighbouring MOTION shots alternate dark and light (the runner decides).
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from .cards import FPS, _find, render_project, _norm
from .io import api, event, save

ROOT = Path(__file__).resolve().parent
W, H = 1920, 1080

LAYOUTS = ("kinetic", "timeline", "stat", "route", "process")
POLARITIES = ("dark", "light")

CONTENT_GROUP = 15
CONTENT_TIMEOUT_SECONDS = 45

# The last second moves slowly and adds nothing new.
IDLE_SECONDS = 1.0
# The time an item needs to land after its word (the longest entrance).
SETTLE_SECONDS = 0.55
# The least time between two beats: an entrance takes 0.35-0.45 s.
GAP = 0.45

MAX_ITEMS = {"kinetic": 3, "timeline": 4, "route": 4, "process": 4}
MIN_ITEMS = {"kinetic": 2, "timeline": 2, "route": 2, "process": 2}
ITEM_WORDS = {"kinetic": 2, "timeline": 3, "route": 3, "process": 3}
ITEM_CHARS = {"kinetic": 14, "timeline": 20, "route": 18, "process": 22}
TITLE_WORDS, TITLE_CHARS = 6, 44
PILL_WORDS, PILL_CHARS = 4, 26
NUMBER_CHARS = 12

STOP = set("""a an the and or but of to in on at by for from with as is was were be been being are this that these those
it its into than then so such his her their our your my he she they we you i not no nor also which who whom whose what when
where while how why after before over under about more most less least very just only had has have would could should will can may
there here up out one some any each every all both few many much own same other""".split())

_UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                     "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {w: 10 * (i + 2) for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}
_SCALES = {"hundred": 100, "thousand": 1000, "million": 10 ** 6, "billion": 10 ** 9}
NUMBER_WORDS = set(_UNITS) | set(_TENS) | set(_SCALES) | {"dozen", "dozens", "percent", "half", "twice", "double", "triple"}
# Ranking claims are facts too: on screen only when the narration says them.
NUMBER_WORDS |= {"first", "second", "third", "last", "only", "largest", "biggest", "longest", "fastest", "oldest", "tallest",
                 "smallest", "highest", "deepest", "earliest"}


def _tokens(text):
    return re.findall(r"[^\s]+", str(text or ""))


def _spelled_numbers(words):
    """The values the narration spells out ("two hundred" -> "200")."""
    found, total, current, active = set(), 0, 0, False
    for raw in [t for w in words for t in str(w).lower().replace("-", " ").split()] + [""]:
        word = re.sub(r"[^a-z]", "", raw)
        if word in _UNITS or word in _TENS:
            value = _UNITS.get(word, 0) + _TENS.get(word, 0)
            if active and not total and 10 <= current < 100 and (word in _TENS or value >= 10):
                # a year said in pairs: "nineteen forty-five", "eighteen seventy-six"
                current = current * 100 + value
            else:
                current += value
            active = True
        elif word == "hundred" and active:
            current *= 100
        elif word in ("thousand", "million", "billion") and active:
            # "twenty million" may be written "20 million" (the scale word is spoken)
            found.add(str(current))
            total += current * _SCALES[word]
            current = 0
        elif word == "and" and active:
            continue
        else:
            if active:
                found.add(str(total + current))
            total, current, active = 0, 0, False
    return found


def _known(words):
    """What the narration says: its words (normalised) and its figures."""
    texts = [w["word"] for w in words]
    norm = {_norm(t) for t in texts if _norm(t)}
    # "patents" covers "patent" and the other way round
    norm |= {n[:-1] for n in norm if n.endswith("s") and len(n) > 3} | {n + "s" for n in norm}
    digits = set(re.findall(r"\d+", " ".join(texts).replace(",", ""))) | _spelled_numbers(texts)
    return norm, digits


def _clean(text, known, max_words, max_chars, strict=False):
    """A label the narration supports, or None.

    Every figure has to be one the narration gives (digits or spelled),
    a number word has to be spoken, and a capitalised word the narration
    does not have is an invented name or place. strict (route places):
    every word has to be the narration's own.
    """
    if not isinstance(text, str):
        return None
    text = re.sub(r"\s+", " ", text).strip().strip(".;:")
    tokens = _tokens(text)
    if not tokens or len(tokens) > max_words or len(text) > max_chars:
        return None
    norm, digits = known
    for token in tokens:
        key = _norm(token)
        if not key:
            continue
        if re.search(r"\d", token):
            if not set(re.findall(r"\d+", token.replace(",", ""))) <= digits:
                return None
        elif key in NUMBER_WORDS or key in norm:
            if key in NUMBER_WORDS and key not in norm:
                return None
        elif strict or (token[:1].isupper() and key not in STOP):
            return None
    return text


def _figure(text, known):
    """A figure (number or year) from the narration, written as one token."""
    text = _clean(text, known, 3, NUMBER_CHARS)
    if not text or not re.search(r"\d", text):
        return None
    return text


def _year(token):
    match = re.fullmatch(r"(\d{4})s?", token)
    return bool(match) and 1000 <= int(match.group(1)) <= 2100


def fallback(words, known=None):
    """Kinetic words taken from the sentence: its 2-3 longest content
    words in spoken order, and its first figure."""
    known = known or _known(words)
    seen, picks = set(), []
    for i, w in enumerate(words):
        key = _norm(w["word"])
        if (key and key not in STOP and key not in NUMBER_WORDS and not re.search(r"\d", key)
                and len(key) >= 4 and key not in seen):
            seen.add(key)
            picks.append((len(key), -i, i))
    chosen = sorted(i for _, _, i in sorted(picks, reverse=True)[:3])
    items = [{"text": re.sub(r"[^\w'’-]", "", words[i]["word"]), "sub": None, "word": words[i]["word"]} for i in chosen]
    number = None
    for w in words:
        token = w["word"].strip(".,;:!?()\"'")
        if re.search(r"\d", token) and _figure(token, known):
            number = {"text": token, "word": w["word"]}
            break
    if number is None:
        spelled = sorted(_spelled_numbers([w["word"] for w in words]), key=lambda v: -len(v))
        if spelled:
            value = int(spelled[0])
            number = {"text": f"{value:,}" if value >= 10000 else str(value), "word": None}
            # it lands on the first number word the narration speaks
            number["word"] = next((w["word"] for w in words if _norm(w["word"]) in NUMBER_WORDS), None)
    if len(items) < 2:
        items = items + [{"text": re.sub(r"[^\w'’-]", "", w["word"]), "sub": None, "word": w["word"]}
                         for w in words if _norm(w["word"]) and w["word"] not in [x["word"] for x in items]][:2 - len(items)]
    return {"layout": "kinetic", "title": None, "items": items[:3], "number": number, "pill": None, "trend": "up"}


def validate(answer, item):
    """A MOTION shot's content, checked against its own narration.

    Returns {layout, polarity, title, items:[{text, sub, at}], number,
    pill, trend, source, issues}; times are shot-local seconds. A layout
    that does not keep enough valid items becomes kinetic with words
    from the sentence.
    """
    words = item["words"]
    known = _known(words)
    issues = []
    answer = answer if isinstance(answer, dict) else {}
    layout = answer.get("layout") if answer.get("layout") in LAYOUTS else None
    if answer and layout is None:
        issues.append("layout")
    spec = None
    if layout:
        title = _clean(answer.get("title"), known, TITLE_WORDS, TITLE_CHARS) if answer.get("title") else None
        if answer.get("title") and title is None:
            issues.append("title")
        number = None
        if isinstance(answer.get("number"), dict) and answer["number"].get("text"):
            text = _figure(str(answer["number"]["text"]), known)
            if text:
                number = {"text": text, "word": answer["number"].get("word")}
            else:
                issues.append("number")
        pill = None
        if isinstance(answer.get("pill"), dict) and answer["pill"].get("text"):
            text = _clean(answer["pill"]["text"], known, PILL_WORDS, PILL_CHARS)
            if text:
                pill = {"text": text, "word": answer["pill"].get("word")}
            else:
                issues.append("pill")
        items = []
        if layout != "stat":
            for k, raw in enumerate(answer.get("items") or []):
                if not isinstance(raw, dict):
                    continue
                text = _clean(raw.get("text"), known, ITEM_WORDS[layout], ITEM_CHARS[layout], strict=layout == "route")
                sub = raw.get("sub")
                if sub not in (None, ""):
                    sub = _figure(str(sub), known)
                    if sub is None:
                        issues.append("item_%d_sub" % k)
                else:
                    sub = None
                if text is None:
                    issues.append("item_%d" % k)
                    continue
                if layout == "timeline" and sub is None:
                    issues.append("item_%d_date" % k)
                    continue
                items.append({"text": text, "sub": sub, "word": raw.get("word")})
            items = items[:MAX_ITEMS[layout]]
        ok = (number is not None) if layout == "stat" else len(items) >= MIN_ITEMS[layout]
        if ok:
            spec = {"layout": layout, "title": title, "items": items, "number": number, "pill": pill,
                    "trend": "down" if answer.get("trend") == "down" else "up"}
        else:
            issues.append("too_few_items" if layout != "stat" else "stat_number")
    if spec is None:
        spec = fallback(words, known)
        source = "fallback"
    else:
        source = "flash"
    spec.update(source=source, issues=issues, polarity=item.get("polarity") if item.get("polarity") in POLARITIES else "dark")
    _times(spec, words, item.get("duration"))
    return spec


def _times(spec, words, duration):
    """Each item lands on its word; a word the narration lacks gets an
    even slot. Everything has landed by duration - IDLE - SETTLE."""
    duration = float(duration or (max((w["end"] for w in words), default=3.0) + 0.5))
    last = max(0.6, duration - IDLE_SECONDS - SETTLE_SECONDS)
    beats = [("item", i) for i in range(len(spec["items"]))] + ([("number", 0)] if spec["number"] else []) + \
            ([("pill", 0)] if spec["pill"] else [])
    found, after = [], 0.0
    for kind, i in beats:
        target = spec["items"][i] if kind == "item" else spec[kind]
        at = _find(words, target.get("word"), after) if target.get("word") else None
        if at is None and kind == "item":
            at = _find(words, target["text"].split()[0], after)
        if at is not None:
            after = at
        found.append(at)
    # an even grid between the first moment (0.35 s) and the last landing
    count = len(beats)
    grid = [0.35 + (last - 0.35) * k / max(1, count - 1) for k in range(count)] if count > 1 else [0.35]
    times, floor = [], 0.25
    for k, at in enumerate(found):
        t = grid[k] if at is None else at - 0.08
        # at least GAP between beats (an entrance is 0.35-0.45 s), room left for the ones after
        t = max(floor, min(t, last - GAP * (count - 1 - k)))
        times.append(round(t, 3))
        floor = t + GAP
    for (kind, i), t in zip(beats, times):
        (spec["items"][i] if kind == "item" else spec[kind])["at"] = t
    spec["title_at"] = 0.15
    spec["duration"] = round(duration, 3)


def _prompt(group, feedback=None):
    return ('Design the on-screen content of documentary MOTION GRAPHICS shots (code-drawn, kinetic typography and '
            'infographics). The viewer hears the narration while the graphic builds; each item appears as its word is '
            'spoken. Choose one layout per shot: '
            'timeline = 2-4 dated items (each with a year/date in sub and a 1-3 word label) when the sentence gives dates; '
            'stat = one striking figure (number) with a short title and an optional pill, when the sentence gives a '
            'quantity, size, cost, count or percentage; trend "up" or "down" says which way it moves; '
            'route = 2-4 named places (1-3 words each, copied exactly) when the sentence moves between places; '
            'process = 2-4 short steps (1-3 words each) when the sentence describes steps, stages or a sequence; '
            'kinetic = 2-3 single power words copied from the sentence, plus an optional number/year, for anything else '
            '(comparisons, ideas, a turning point). '
            'STRICT: every number, year, name and place must appear in the shot narration itself (a spelled number may be '
            'written in digits, e.g. "two hundred" -> "200"); never add a fact, date, figure, name or place the narration '
            'does not say. Copy words in the case the narration uses. English text. title: optional heading of at most '
            '6 words (stat: what the figure counts). Every item and the number/pill carry word: the narration word it '
            'lands on, copied exactly. '
            'Return JSON {shots:[{shot_id,layout,title,items:[{text,sub,word}],number:{text,word}|null,'
            'pill:{text,word}|null,trend}]}, every requested shot_id once; use null for absent fields. '
            + ("Earlier versions of these graphics were rejected; fix this: %s " % json.dumps(feedback, ensure_ascii=False)[:1200]
               if feedback else "")
            + 'SHOTS:' + json.dumps([{"shot_id": i["shot_id"], "narration": " ".join(w["word"] for w in i["words"])}
                                     for i in group], ensure_ascii=False))


def contents(items, folder, feedback=None):
    """Content for a batch of MOTION shots, one Flash call per group.

    items: [{shot_id, words, duration, polarity}]. A group whose call
    fails, or a shot the answer leaves out, gets the kinetic fallback
    from its own sentence, so a shot is never lost to its text.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    def group(entry):
        index, batch = entry
        receipt = folder / f"motion_content_{index:02}.json"
        try:
            rows = api("flash", _prompt(batch, feedback), receipt, tokens=500 + 320 * len(batch),
                       timeout=CONTENT_TIMEOUT_SECONDS,
                       deadline=time.monotonic() + 2 * CONTENT_TIMEOUT_SECONDS)["data"].get("shots")
        except Exception as exc:
            rows = []
            event(folder, "motion_content_fallback", group=index, shots=len(batch), error=type(exc).__name__)
        given = {}
        for r in rows if isinstance(rows, list) else []:
            if isinstance(r, dict):
                given.setdefault(r.get("shot_id"), r)
        return {i["shot_id"]: validate(given.get(i["shot_id"]), i) for i in batch}

    groups = [items[i:i + CONTENT_GROUP] for i in range(0, len(items), CONTENT_GROUP)]
    if not groups:
        return {}
    with ThreadPoolExecutor(max_workers=max(1, min(len(groups), int(os.environ.get("DOCUMENTARY_FLASH_CONCURRENCY", "10"))))) as pool:
        return {k: v for answer in pool.map(group, enumerate(groups)) for k, v in answer.items()}


# ------------------------------------------------------------------ layout
# Montserrat 800-900 runs ~0.68 em per mixed-case character (cards.py);
# 0.72 leaves a margin, and capitals run wider.
def _em(text):
    caps = sum(1 for c in text if c.isupper() or c.isdigit())
    thin = sum(1 for c in text if c in ",.:;'’ ")
    return 0.62 * (len(text) - caps - thin) + 0.78 * caps + 0.3 * thin + 0.1


def _fit(text, width, largest, smallest=24):
    return int(max(smallest, min(largest, width / max(1.0, _em(text)))))


def _lines(text, max_lines=2):
    """A label as one or two lines, split at the word nearest the middle."""
    words = text.split()
    if len(words) < 2 or max_lines < 2:
        return [text]
    best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
    return [" ".join(words[:best]), " ".join(words[best:])]


def _count_steps(token, start, land):
    """A count-up as (time, text) steps that keep the token's own format;
    a year counts from 60 years before it."""
    match = re.search(r"\d[\d,]*(\.\d+)?", token)
    if not match:
        return [[round(start, 3), token]]
    prefix, number, suffix = token[:match.start()], match.group(0), token[match.end():]
    value = float(number.replace(",", ""))
    decimals = len(match.group(1)) - 1 if match.group(1) else 0
    begin = max(0.0, value - 60) if _year(number + ("s" if suffix == "s" else "")) else 0.0
    steps = max(2, min(18, int((land - start) * FPS)))
    out = []
    for k in range(steps + 1):
        v = begin + (value - begin) * (1 - (1 - k / steps) ** 3)
        text = f"{v:,.{decimals}f}" if "," in number else f"{v:.{decimals}f}"
        out.append([round(start + (land - start) * k / steps, 3), prefix + text + suffix])
    out[-1][1] = token
    return out


def layout(spec, count):
    """The template's configuration: sizes in pixels, times in seconds."""
    duration = count / FPS
    spec = json.loads(json.dumps(spec))
    if abs(spec.get("duration", duration) - duration) > 0.02:
        # the content was timed for another length; keep the order, rescale
        scale = duration / spec["duration"]
        for target in spec["items"] + [x for x in (spec.get("number"), spec.get("pill")) if x]:
            target["at"] = round(target["at"] * scale, 3)
    lay = spec["layout"]
    # The words keep the narration's case (validate); on screen a heading
    # and every item start with a capital, as in the approved builds.
    if spec.get("title"):
        spec["title"] = spec["title"][:1].upper() + spec["title"][1:]
    for it in spec["items"]:
        it["text"] = it["text"][:1].upper() + it["text"][1:]
    config = {"layout": lay, "polarity": spec["polarity"], "duration": round(duration, 3),
              "idle": round(max(0.8, duration - IDLE_SECONDS), 3), "title": None, "items": [], "number": None,
              "pill": None, "trend": spec.get("trend", "up")}
    if spec.get("title"):
        config["title"] = {"text": spec["title"], "at": spec.get("title_at", 0.15), "size": _fit(spec["title"], 1500, 64, 30)}
        if lay == "stat":
            # the headline left of the metric card, in one or two lines
            lines = _lines(spec["title"])
            config["title"].update(lines=lines, size=min(_fit(line, 900, 96, 40) for line in lines))
    n = len(spec["items"])
    for k, it in enumerate(spec["items"]):
        entry = {"text": it["text"], "sub": it.get("sub"), "at": it["at"], "index": "%02d" % (k + 1)}
        if lay == "kinetic":
            entry["size"] = _fit(it["text"], 1680, 200, 90)
        elif lay in ("timeline", "process"):
            width = (1620 - 60 * (n - 1)) / n - 80
            entry["lines"] = _lines(it["text"])
            entry["size"] = min(_fit(line, width, 60, 26) for line in entry["lines"])
            if it.get("sub"):
                entry["sub_size"] = _fit(it["sub"], width, 72 if lay == "timeline" else 40, 28)
        elif lay == "route":
            width = min(420, 1500 / n)
            entry["lines"] = _lines(it["text"])
            entry["size"] = min(_fit(line, width, 50, 26) for line in entry["lines"])
        config["items"].append(entry)
    number = spec.get("number")
    if number:
        land = number["at"] + (1.0 if lay == "kinetic" else 1.2)
        land = min(land, config["idle"] - 0.05)
        start = min(number["at"] + 0.05, land - 0.3)
        config["number"] = {"text": number["text"], "at": number["at"],
                            "size": _fit(number["text"], 1600 if lay == "kinetic" else 540, 300 if lay == "kinetic" else 180, 80),
                            "steps": _count_steps(number["text"], start, land)}
    if spec.get("pill"):
        config["pill"] = {"text": spec["pill"]["text"], "at": spec["pill"]["at"], "size": _fit(spec["pill"]["text"], 440, 40, 22)}
    return config


def write_project(spec, count, work):
    """A HyperFrames project for one MOTION shot: the template with its values in."""
    project = Path(work) / "motion_project"
    (project / "vendor").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "three_vendor" / "gsap.min.js", project / "vendor" / "gsap.min.js")
    config = layout(spec, count)
    source = (ROOT / "motion_template.html").read_text(encoding="utf8")
    title = re.sub(r"[<>&\"]", "", (spec.get("title") or " ".join(i["text"] for i in spec["items"]) or "Motion"))[:60]
    source = (source.replace("__TITLE__", title).replace("__DURATION__", str(config["duration"]))
              .replace("__CONFIG__", json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")))
    (project / "index.html").write_text(source, encoding="utf8")
    save(project / "hyperframes.json", {"paths": {"assets": "assets"}})
    save(project / "motion_config.json", config)
    return project


def render_motion(asset, count, output, work):
    """Render one MOTION shot to output at exactly count frames of 25 fps.

    Rendered the way cards are (render_card): HyperFrames with one browser
    and screenshot capture under the shared hyperframes slot, then encoded
    once more with the pipeline's encoder for the stream-copy concat.
    Returns the layout name.
    """
    from .three_render import _governor, encoding_slot
    from .io import run
    if type(count) is not int or count <= 0:
        raise ValueError("A motion graphic needs a positive frame count")
    work = Path(work)
    project = write_project(asset["motion"], count, work)
    raw = work / "motion_raw.mp4"
    with _governor().slot("hyperframes"):
        render_project(project, raw, count)
    with encoding_slot() as encoder:
        run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vf", "fps=25,setsar=1,tpad=stop_mode=clone:stop_duration=1",
             "-frames:v", count, "-an", *encoder, "-pix_fmt", "yuv420p", "-movflags", "+faststart", output], 180)
    save(work / "motion_receipt.json", {"layout": asset["motion"]["layout"], "polarity": asset["motion"]["polarity"],
                                        "project": str(project), "frame_count": count})
    return asset["motion"]["layout"]
