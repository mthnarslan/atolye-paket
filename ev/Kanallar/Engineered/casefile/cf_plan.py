"""Step 1: editorial plan (cf_plan.json): GPT drafts, code validates. Facts on cards must trace to the script/fact sheet."""
import re, sys
from cf_common import *

MODES = ("FULL", "COLLAGE", "PRINT", "MONITOR")
KINDS = {"document": ("header", "lines"), "number": ("value", "label"), "datetime": ("text",), "map": ("from", "to"),
         "quote": ("text",), "compare": ("a", "b")}
STYLE = ("STYLE (locked): hand-drawn vintage engraving illustration brought to life, fine black ink crosshatching on aged cream paper, "
         "layered paper-cut diorama depth, muted palette with a single deep red accent, soft film grain, calm documentary tone. "
         "No text, no letters, no logos, no visible human faces.")


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", str(s).lower().replace("’", "'")).split()


def digits_in(s):
    return set(t.replace(",", "").rstrip(".") for t in re.findall(r"\d[\d,]*\.?\d*", str(s)))


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def cut(x, n):
    x = str(x)
    return x if len(x) <= n else x[:n].rsplit(" ", 1)[0]


DANGLE = {"and", "or", "of", "the", "a", "an", "to", "in", "on", "at", "for", "with", "by", "from", "is", "was", "than", "that"}


def good_value(v):
    """A document value must be complete: >= 2 words or a number, not ending on a dangling function word."""
    w = str(v).strip().split()
    return bool(w) and (len(w) >= 2 or bool(re.search(r"\d", w[0]))) and w[-1].lower().strip(".,;:") not in DANGLE and bool(re.search(r"[A-Za-z0-9]{2}", v))


def clean_document(c):
    """Keep only fields with a label and a complete value (remapping rings/strike); False when fewer than 2 fields survive (card is dropped, never rendered half-empty)."""
    keep = []
    for k, x in enumerate(map(str, c.get("lines") or [])):
        lab, _, val = re.sub(r"\.{2,}", "..", x).partition("..")
        if re.search(r"[A-Za-z]{2}", lab) and good_value(val.strip(". ")) and len(x) <= 46: keep.append(k)
    c["lines"] = [re.sub(r"\.{4,}", "...", str(c["lines"][k])) for k in keep]
    for f in ("rings", "strike"):
        c[f] = [keep.index(i) for i in c.get(f, []) if isinstance(i, int) and i in keep]
    return len(keep) >= 2


def prompt(F, cand):
    heads = re.findall(r"^### (.+)$", F["script"], re.M)
    rows = "\n".join(f'{r["i"]}|{r["start"]:.1f}|{r["end"]-r["start"]:.1f}|{r["cat"]}|{"clip" if r["clip"] else "MISSING"}{"|FLAG" if r["flagged"] else ""}|{r["narr"]}'
                     for r in F["rows"])
    return f"""You are the editor of a documentary channel "WRATH OF EARTH" (dark topographic "case file" look). Film: {F['title']}
Plan the edit of a finished film. Script section headings: {heads}
EDL rows (index|start s|dur s|category|clip state|narration fragment). Total {F['total']:.0f} s:
{rows}

Return ONE JSON object, no commentary:
{{"sections":[{{"first_row":1,"kicker":"HOOK","title":"","tease":"","mode":"FULL"}}, ... 4-6 parts ..., epilogue],
 "cards":[{{"rows":[a,b],"kind":"document|number|datetime|map|quote|compare", ...fields...}}],
 "lower_thirds":[{{"row":i,"kicker":"Friday, June 20, 2025","line":"Richland County, North Dakota","offset":0.6}}],
 "flow":[{{"row":i,"action":"one sentence of camera motion and scene"}}],
 "memorial":null}}
Rules:
- sections: first is the hook (kicker HOOK, mode FULL, no title); then parts (kicker "PART I".., title <=4 words, optional "tease" = a short wrong claim the film refutes, quoted from the script, shown struck through), last is the epilogue (kicker EPILOGUE, FULL). mode in FULL|COLLAGE|PRINT|MONITOR, vary between neighbours. first_row ascending.
- cards REPLACE weak rows (category MOTION/CARD, MISSING clips, one-word cards, TV-graphic/news-logo clips) with our own graphic over rows a..b (<=2 rows, <=9 s). About 1 card per 25 s, including inside the first 90 s. Fields per kind:
  document: header (agency/title line), lines (3-6 short strings, each <=38 chars, "LABEL ........ value"), rings (list of 0-based line indexes to circle in red pen), strike (0-based line indexes struck through), note (handwritten <=5 words, optional)
  number: kicker, value (e.g. "107"), unit (e.g. "MPH"), label, source (short, optional)
  datetime: kicker, text (e.g. "8:49 PM"), place
  map: from, to, label, distance (e.g. "165.6 mi")     compare: title, a {{label,value(number)}}, b {{label,value}}, unit     quote: text (<=22 words, verbatim from the script), by
- FACTS ONLY from the narration/script of that card's own rows: never invent numbers, names, quotes. Documents are "illustrative layout".
- lower_thirds: 20-25 over the film, only when the narration states a place and/or time (that row); kicker=time or context, line=place. English.
- flow: ACTION lines only for these candidate rows (hook rows and rows flagged for text/watermark), max 10: {cand}. No real people, no text in scene.
- memorial: if the film is about deaths, {{"text":"In memory of the N people killed ..."}} calm, wording from the script; else null."""


def validate(plan, F):
    n, rows, warn = len(F["rows"]), F["rows"], []
    ok_dig = digits_in(F["script"]) | digits_in(F["fact"]) | digits_in(" ".join(r["narr"] for r in rows))
    sec = []
    for s in plan.get("sections") or []:
        try:
            sec.append(dict(first_row=max(1, min(n, int(s["first_row"]))), kicker=str(s.get("kicker") or "")[:24], title=str(s.get("title") or "")[:40],
                            tease=str(s.get("tease") or "")[:60], mode=s.get("mode") if s.get("mode") in MODES else "PRINT"))
        except Exception:
            warn.append(f"bad section {s}")
    sec.sort(key=lambda s: s["first_row"])
    if not sec or sec[0]["first_row"] != 1:
        sec.insert(0, dict(first_row=1, kicker="HOOK", title="", tease="", mode="FULL"))
    sec[0].update(mode="FULL", title="", tease="")
    if len(sec) > 2:
        sec[-1]["mode"] = "FULL"
    cards, used = [], set()
    for c in plan.get("cards") or []:
        try:
            a, b = (list(c["rows"]) + [c["rows"][0]])[:2]
            a, b = max(1, int(a)), min(n, int(b))
            k = c["kind"]; need = KINDS[k]
            if b < a or b - a > 1 or any(not c.get(x) for x in need) or used & set(range(a, b + 1)):
                raise ValueError("shape/overlap")
            if sum(rows[j]["end"] - rows[j]["start"] for j in range(a - 1, b)) > 9.5:
                raise ValueError("too long")
            blank = lambda v: not any(re.search(r"[A-Za-z0-9]", x) for x in strings(v))
            if any(blank(c[x]) for x in need):
                raise ValueError("blank field")
            if k == "document" and not clean_document(c):
                raise ValueError("document with <2 complete fields")
            facts = {x: v for x, v in c.items() if x not in ("rows", "kind", "rings", "strike")}
            bad = [d for d in digits_in(" ".join(strings(facts))) if d not in ok_dig]
            if bad:
                raise ValueError(f"numbers not in script: {bad}")
            if k == "quote" and " ".join(norm(c["text"])) not in " ".join(norm(F["script"])):
                raise ValueError("quote not verbatim")
            if k == "compare":
                float(c["a"]["value"]); float(c["b"]["value"])
            c["rows"] = [a, b]; cards.append(c); used |= set(range(a, b + 1))
        except Exception as e:
            warn.append(f"card dropped ({e}): {str(c)[:90]}")
    lts = []
    for l in plan.get("lower_thirds") or []:
        try:
            r = int(l["row"]); assert 1 <= r <= n
            lts.append(dict(row=r, kicker=str(l.get("kicker") or "")[:44], line=str(l["line"])[:52], offset=float(l.get("offset", .6))))
        except Exception:
            warn.append(f"lt dropped {l}")
    hook_end = sec[1]["first_row"] if len(sec) > 1 else 0
    cand = {r["i"] for r in rows if r["i"] < hook_end} | {r["i"] for r in rows if r["flagged"]}
    flow = [dict(row=int(f["row"]), action=str(f["action"])[:300]) for f in plan.get("flow") or [] if str(f.get("row", "")).isdigit() and int(f["row"]) in cand][:12]
    mem = plan.get("memorial")
    if mem and not (isinstance(mem, dict) and mem.get("text") and len(mem["text"].split()) <= 24 and digits_in(mem["text"]) <= ok_dig):
        mem = None
    return dict(film=F["film"], title=F["title"], sections=sec, cards=cards, lower_thirds=lts, flow=flow, memorial=mem, warnings=warn)


def default_plan(F):
    """Offline fallback: even parts, alternating modes, no cards."""
    n = len(F["rows"]); hook = next((r["i"] for r in F["rows"] if r["start"] >= 45), 2)
    cuts = [hook + round((n - hook) * k / 5) for k in range(5)]
    modes = ["COLLAGE", "PRINT", "MONITOR", "PRINT", "COLLAGE"]
    sec = [dict(first_row=1, kicker="HOOK", title="", tease="", mode="FULL")]
    sec += [dict(first_row=c, kicker="PART " + ["I", "II", "III", "IV", "V"][k], title=f"Part {k + 1}", tease="", mode=modes[k]) for k, c in enumerate(cuts)]
    return dict(sections=sec, cards=[], lower_thirds=[], flow=[], memorial=None)


def make_plan(F, W, force=False):
    f = W / "cf_plan.json"
    if f.exists() and not force:
        old = jload(f)   # stale if drafted against another EDL (row count changed)
        n = len(F["rows"])
        old["cards"] = [c for c in old["cards"] if c["kind"] != "document" or clean_document(c)]
        if all(s["first_row"] <= n for s in old["sections"]) and all(c["rows"][1] <= n for c in old["cards"])                 and all(l["row"] <= n for l in old["lower_thirds"]):
            return old
        print("  cached plan does not fit", n, "rows; redrafting")
    hook_end = next((r["i"] for r in F["rows"] if r["start"] >= 45), 8)
    cand = [r["i"] for r in F["rows"] if r["i"] < hook_end or r["flagged"]]
    raw = {}
    for attempt in range(2):
        txt = llm(prompt(F, cand))
        (W / "plan_raw.txt").write_text(txt, encoding="utf8")
        try:
            raw = json_from(txt); break
        except Exception as e:
            print("  plan JSON parse failed:", e, txt[:120])
    if not raw:
        print("  using default_plan (LLM unavailable)"); raw = default_plan(F)
    plan = validate(raw, F); jsave(f, plan)
    for w in plan["warnings"]:
        print("  warn:", w)
    return plan


def extend_flow(F, plan, W, weak):
    """Rows whose visual check found a mark that no <=12% edge crop removes get a Flow replacement too (ACTION line drafted by Flash from that row's narration/scene text)."""
    have = {f["row"] for f in plan["flow"]}
    need = [r for r in F["rows"] if r["clip"] and r["flagged"] and not r["crop"] and r["i"] not in weak and r["i"] not in have]
    if not need: return
    sys.path.insert(0, r"C:\Users\meteh\SkullStudio\pipeline")
    from common import flash
    q = ("For each documentary shot write ONE sentence (<=25 words) of camera motion and scene for an engraving-style illustrated clip that shows what the narration describes. "
         "No people, no text, no signs, no logos. Shots (row|narration|scene):\n" + "\n".join(f'{r["i"]}|{r["narr"]}|{r["scene"][:200]}' for r in need) +
         '\nJSON only: {"<row>": "action sentence", ...}')
    try: acts = flash(q)
    except Exception as e:
        print("  flow actions: Flash failed", str(e)[:80]); acts = {}
    for r in need:
        a = acts.get(str(r["i"])) or f'Slow push-in on a quiet illustrated scene of: {r["narr"][:140]}'
        plan["flow"].append(dict(row=r["i"], action=str(a)[:300]))
    jsave(W / "cf_plan.json", plan); print(f"  flow: +{len(need)} replacements for rows with marks {[r['i'] for r in need]}")
