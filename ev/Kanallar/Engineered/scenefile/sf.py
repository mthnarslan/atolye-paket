"""WRATH OF EARTH script-first edit (the logic of the 1-min Enderlin sample): every sentence or beat is a designed scene; real clips only where they show
exactly what is said. usage: python sf.py FILM plan|prep|build|render|mix|all [--range A B]  (FILM = CodexOutputs folder name)"""
import argparse, json, math, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "casefile"))
from cf_common import load_film, llm, json_from, check_rows, clip_check, ffmpeg, wait_ram, free_gb, jload, jsave, DELIVERY   # noqa: E402
import cf_audio as A                                                                                              # noqa: E402
import sf_scenes as S                                                                                             # noqa: E402

SAMPLE = HERE.parent / "ornek" / "woe_sample" / "assets"
HF = "hyperframes@0.8.181"
FPS = 25
END_CARD = 6.0
CHUNK = 55.0            # seconds per HyperFrames render chunk (55: finer split across PC/a1/vds slots)


def W(film):
    return Path(os.environ["SF_WORK_DIR"]) / film if os.environ.get("SF_WORK_DIR") else HERE / "work" / film


def case_label(film, script):
    num = re.match(r"EP0*(\d+)", film).group(1)
    loc = re.sub(r"\d{4}", "", film.split("_", 1)[1]).replace("_", " ").strip().upper()
    return f"CASE FILE {int(num):02d} · {loc}"


# -------------------------------------------------------------------------------------------- catalog
def catalog(F, cache, fl):
    rows = F["rows"]
    cat = {}
    for r in rows:
        if not r["clip"] or r["review_flag"]:
            continue
        rj = F["out"] / "shots" / f'{r["shot_id"]:04d}' / "result.json"
        desc = ""
        try:
            desc = ((jload(rj).get("review") or {}).get("data") or {}).get("summary") or ""
        except Exception:
            pass
        img = Path(r["clip"]).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        cat[f'R{r["i"]}'] = dict(id=f'R{r["i"]}', src=r["clip"], crop=r["crop"], kind="3D" if r["cat"] in ("3D", "ANIM") else ("PHOTO" if img else "FOOTAGE"),
                                 t=round((r["start"] + r["end"]) / 2, 1), desc=desc[:220], narr=(r["narr"] or "")[:160], img=img)
    plan = jload(fl.parent / "cf_plan.json") if (fl.parent / "cf_plan.json").exists() else {}
    acts = {f["row"]: f["action"] for f in plan.get("flow", [])}
    for f in sorted(q for q in fl.glob("row*.mp4") if re.fullmatch(r"row\d+", q.stem)) if fl.exists() else []:
        k = int(f.stem[3:]); r = rows[k - 1]
        cat[f"F{k}"] = dict(id=f"F{k}", src=str(f), crop=None, kind="ENGRAVING", t=round((r["start"] + r["end"]) / 2, 1),
                            desc="engraving-style illustration: " + acts.get(k, r["narr"][:120]), narr=r["narr"][:160], img=False)
    return cat


# -------------------------------------------------------------------------------------------- planning
RULES = """You are the editor of WRATH OF EARTH, a premium documentary channel. Style = a 'case file': dark topographic map table, evidence prints,
typed official documents with a red pen ring, huge numbers with a red underline, plan-view diagrams, a monitor for radar/data, engraving-style
illustration clips full-frame, title cards. Script-first: every scene is DESIGNED for what the narration says at that moment. No fixed shot length,
no quotas. A real clip is used only if its description shows exactly what is said; otherwise design a graphic scene.

SCENE TYPES (fields):
- full {clips:[id] or [id,id], kicker, line}   full-frame clip with letterbox; kicker+line = short lower-third (place/time/what), may be empty
- print {clips:[id] or [id,id], kicker, line}  clip as a paper evidence print on the map table (2nd print lands on the scene's 2nd sentence)
- print_number {clips:[id], number, unit, label, source, at}   print + a big number beside it (at = index of the sentence inside the scene where the number is said, 0-based)
- number {kicker, number, unit, label, sub, at}  a huge number/year centred
- document {header, title, lines:[[key,value],...max 5], ring:idx or null, strike:idx or null, note}  typed official-style record (warning, rating, survey, report); ring = the key line; note = 2-4 handwritten words
- monitor {clips:[id], kicker, line}  clip on a monitor (radar, data, satellite, computer model, 3D renders)
- map {kicker, title, stops:[2-5 short place/time labels], note}  plan-view route/path diagram
- compare {kicker, title, items:[[label, numeric value, display text],...2-4]}  bars comparing numbers said in the narration
- datetime {kicker, time, line}  a clock time or date being stated ("3:39 PM")
- statement {kicker, text, strike}  ONE punchy phrase of max 4 words (optionally a struck-through wrong idea above it)
- questions {items:[2-3 short questions]}  open questions
- title {kicker, title, subtitle, strike}  a section/part title card (kicker like "PART II", title 1-3 words)
- memorial {text}  one quiet line for the people killed (only if the narration mentions deaths)

HARD RULES:
- Scenes cover the given sentences in order, every sentence exactly once: each scene = {"s": first sentence idx, "e": last idx, "type":..., fields}.
- A scene is 1-4 sentences and normally 4-14 s long; no scene over 18 s.
- Every number/date/name shown must be said in those sentences (or be in the script). Write numbers as digits ("300", "2,250", "EF4", "3:39 PM").
- Texts are SHORT: kicker <= 4 words, line <= 7 words, label <= 6 words. English. No sentence copied as on-screen text.
- Clips: use only ids from the catalog; never reuse an id; prefer clips whose time t is near the sentence time; FOOTAGE for real events, ENGRAVING for
  scenes nobody filmed (history, people, mood), 3D only inside monitor. PHOTO only in print.
- Variety: never the same type 3 times in a row; about half the scenes use clips; a document or number is a moment, not every scene.
Reply JSON only: {"scenes":[...]}"""


def safe_rect(marks, m=.03, smin=.62):
    """largest 16:9 window (normalized x0,y0,s) that keeps every mark box (+margin) out of frame, or None; used only for small frames (print/collage/monitor)"""
    import itertools
    boxes = [b for b in (q.get("box") for q in marks) if isinstance(b, list) and len(b) == 4]
    if not boxes or len(boxes) != len(marks) or len(boxes) > 4:
        return None
    best = None
    for combo in itertools.product(range(4), repeat=len(boxes)):
        X0, Y0, X1, Y1 = 0., 0., 1., 1.
        for (bx0, by0, bx1, by1), c in zip(boxes, combo):
            if c == 0: Y0 = max(Y0, by1 + m)
            elif c == 1: Y1 = min(Y1, by0 - m)
            elif c == 2: X0 = max(X0, bx1 + m)
            else: X1 = min(X1, bx0 - m)
        sz = min(X1 - X0, Y1 - Y0)
        if sz >= smin and (best is None or sz > best[2]):
            best = (X0 + (X1 - X0 - sz) / 2, Y0 + (Y1 - Y0 - sz) / 2, sz)
    return [round(v, 4) for v in best] if best else None


def jparse(text, want=None):
    """First JSON object/array in an LLM reply (fences, preamble, trailing prose tolerated); `want` = a key the object must hold (an inner object of a broken
    outer one is skipped). Unquoted keys / trailing commas (no-thinking answers sometimes write `ring:3,strike:2,note":`) get one regex repair.
    Raises ValueError with a readable reason. Was: re.search(...).group() -> "'NoneType' object has no attribute 'group'" whenever GPT answered with an error string."""
    text = text if isinstance(text, str) else ""
    dec = json.JSONDecoder()
    def scan(t):
        for m in re.finditer(r"[\{\[]", t):
            try:
                r = dec.raw_decode(t[m.start():])[0]
            except ValueError:
                continue
            if want is None or (isinstance(r, dict) and r.get(want)):
                return r
        return None
    r = scan(text)
    if r is None:
        fixed = re.sub(r",\s*([\}\]])", lambda m: m.group(1), re.sub(r'([\{,]\s*)"?([A-Za-z_]\w*)"?\s*:', lambda m: f'{m.group(1)}"{m.group(2)}":', text))
        r = scan(fixed)
    if r is None:
        raise ValueError(f"no JSON{' with ' + want if want else ''} in reply ({len(text)} chars: {text[:60]!r})")
    return r


FAST = os.environ.get("SF_PLAN_FAST", "1") != "0"                  # 0 = old behaviour (thinking Flash, GPT hedge, 6 workers, per-clip check)
FAST_EFFORT = os.environ.get("SF_PLAN_EFFORT", "minimal")
FAST_TO = float(os.environ.get("SF_FAST_TIMEOUT", 60))              # one no-thinking request: 5-12 s measured, 60 s = 5x margin
FAST_TRIES = int(os.environ.get("SF_FAST_TRIES", 3))


def flash_t(p, model, timeout, effort=None, want=None):
    """common.flash with a short per-request timeout (common.flash waits 300 s on a hung gateway). effort="minimal" sends reasoning_effort: the gateway then
    skips the hidden thinking pass (plan chunk: 154-210 s -> 5-12 s, measured)."""
    import requests
    sys.path.insert(0, r"C:\Users\meteh\SkullStudio\pipeline")
    import common
    body = {"model": model, "messages": [{"role": "user", "content": [{"type": "text", "text": p}]}], "stream": False}
    if effort:
        body["reasoning_effort"] = effort
    r = requests.post(common.F["base_url"].rstrip("/") + "/chat/completions", headers={"Authorization": "Bearer " + common.F["api_key"]}, json=body, timeout=timeout)
    if r.status_code >= 500:
        raise RuntimeError(f"HTTP {r.status_code}")
    raw = r.text
    if raw.lstrip().startswith("data:"):
        parts = [json.loads(l[5:]) for l in raw.splitlines() if l.startswith("data:") and l[5:].strip() not in ("", "[DONE]")]
        text = "".join((q["choices"][0].get("delta") or {}).get("content") or "" for q in parts if q.get("choices"))
    else:
        text = json.loads(raw)["choices"][0]["message"]["content"]
    return jparse(text, want)


GPT_DELAY = float(os.environ.get("SF_GPT_DELAY", 40))       # GPT (4 lanes shared by every film) joins only if Flash has not answered by then
FLASH_TO = float(os.environ.get("SF_FLASH_TIMEOUT", 240))    # thinking Flash request (fallback tier): a plan chunk's thinking pass takes 150-210 s, the old 75 s always timed out


def race(p, key, timeout=400):
    """Flash-high first (short timeout, retried on 502/timeout/bad JSON); GPT hedges after GPT_DELAY s or as soon as Flash is out of tries.
    First valid JSON with `key` wins. Keeps GPT lanes free for stage 3 when Flash is healthy."""
    import concurrent.futures as cf, threading
    t0 = time.time(); done = threading.Event(); err = []
    def valid(r):
        return isinstance(r, dict) and r.get(key)
    def fl():
        for k in range(2):
            if done.is_set():
                return None
            try:
                r = flash_t(p, "ag/gemini-3.8-flash-low", FLASH_TO)
                if valid(r):
                    return r
                err.append(f"flash: no {key}")
            except Exception as e:
                err.append(f"flash try {k}: {str(e)[:60]}")
        return None
    def gpt():
        while not done.is_set() and time.time() - t0 < GPT_DELAY and not fut_flash.done():
            time.sleep(0.5)
        if done.is_set():
            return None
        return jparse(llm(p, timeout=max(60, timeout - (time.time() - t0))))
    ex = cf.ThreadPoolExecutor(2)
    fut_flash = ex.submit(fl); futs = {fut_flash: "flash", ex.submit(gpt): "gpt"}
    try:
        for f in cf.as_completed(futs, timeout=timeout + 30):
            try:
                r = f.result()
                if valid(r):
                    done.set(); print(f"   ({futs[f]} won {time.time() - t0:.0f}s)", flush=True); return r
                if r is not None:
                    err.append(f"{futs[f]}: no {key}")
            except Exception as e:
                err.append(f"{futs[f]}: {str(e)[:80]}")
    except cf.TimeoutError:
        err.append("timeout")
    finally:
        done.set(); ex.shutdown(wait=False, cancel_futures=True)
    raise RuntimeError("; ".join(err))


def plan_sections(F, sents):
    txt = "\n".join(f"{k}: [{a:.0f}s] {t}" for k, (a, b, t) in enumerate(sents))
    p = (f"Documentary narration '{F['title']}', {len(sents)} sentences. Split it into a HOOK (the first ~20-45 s), then 4-6 PARTS and an optional EPILOGUE, "
         f"at real turns of the story. Reply JSON only: {{\"sections\":[{{\"s\": first sentence idx, \"kicker\": \"HOOK\"|\"PART I\"..|\"EPILOGUE\", \"title\": \"1-3 words\"}}]}}\n\n{txt}")
    def go():
        if FAST:
            try:
                return race_fast(p, "sections")
            except Exception as e:
                print(f"  sections: fast path failed ({str(e)[:80]}), thinking race", flush=True)
        return race(p, "sections")
    secs = go()["sections"]
    secs = sorted({int(x["s"]): x for x in secs}.values(), key=lambda x: int(x["s"]))
    secs[0]["s"] = 0
    return secs


def plan_chunk(F, sents, s0, s1, sec, cat):
    a0, a1 = sents[s0][0], sents[s1][1]
    near = [c for c in cat.values() if c["kind"] == "ENGRAVING" or a0 - 90 <= c["t"] <= a1 + 90]
    cl = "\n".join(f'{c["id"]} [{c["kind"]}, t={c["t"]}s] {c["desc"] or "(no description)"} | narration there: {c["narr"]}' for c in near)
    st = "\n".join(f"{k}: [{sents[k][0]:.1f}-{sents[k][1]:.1f}s] {sents[k][2]}" for k in range(s0, s1 + 1))
    head = (f'This section is {sec["kicker"]} "{sec.get("title","")}". ' +
            ("Start it with a title scene covering its first sentence (kicker = the section kicker). " if sec["kicker"] != "HOOK" else
             "This is the cold open: hit hard, a big number or a strong clip first; end the hook with a title scene of the film's short name if a sentence fits."))
    p = f"{RULES}\n\nFILM: {F['title']}\n{head}\n\nSENTENCES:\n{st}\n\nCLIP CATALOG:\n{cl}\n\nSCRIPT FACTS (numbers allowed):\n{F['fact'][:3500]}"
    def go():
        if FAST:
            try:
                return fast_chunk(p, sents, s0, s1)
            except Exception as e:
                print(f"  plan chunk {s0}-{s1}: fast path failed ({str(e)[:100]}), thinking race", flush=True)
        for k in range(3):
            try:
                return race(p, "scenes")["scenes"]
            except Exception as e:
                print(f"  plan chunk {s0}-{s1} retry {k}: {str(e)[:120]}", flush=True)
        return []
    return plan_cached(F["film"], p, go)


def race_fast(p, key):
    """No-thinking Flash-low (reasoning_effort=minimal), several tries; uses no GPT lane. Raises when every try failed."""
    import concurrent.futures as cf
    err = []
    for k in range(FAST_TRIES):                       # each try = 2 identical requests in parallel (~8 s each): a malformed answer is ~1 in 3 on some chunks
        ex = cf.ThreadPoolExecutor(2)
        futs = [ex.submit(flash_t, p, "ag/gemini-3.8-flash-low", FAST_TO, FAST_EFFORT, key) for _ in range(2)]
        try:
            for f in cf.as_completed(futs, timeout=FAST_TO + 15):
                try:
                    r = f.result()
                    if isinstance(r, dict) and r.get(key):
                        return r
                    err.append(f"fast try {k}: no {key}")
                except Exception as e:
                    err.append(f"fast try {k}: {str(e)[:70]}")
        except cf.TimeoutError:
            err.append(f"fast try {k}: timeout")
        finally:
            ex.shutdown(wait=False, cancel_futures=True)
    raise RuntimeError("; ".join(err[-4:]))


def lint_chunk(scenes, sents, s0, s1):
    """(hard, soft) problems of a raw chunk answer. hard = unusable (rerun with thinking); soft = rule slips the model can fix when told."""
    if not isinstance(scenes, list) or not all(isinstance(x, dict) for x in scenes):
        return ["not a list of scenes"], []
    n = s1 - s0 + 1
    hard = [] if len(scenes) >= max(2, 0.3 * n) else [f"only {len(scenes)} scenes for {n} sentences"]
    soft = []
    try:
        sc = sorted(scenes, key=lambda x: int(x["s"]))
        ty = [x.get("type") for x in sc]
        for i in range(2, len(sc)):
            if ty[i] == ty[i - 1] == ty[i - 2]:
                soft.append(f"three '{ty[i]}' scenes in a row (from sentence {sc[i - 2]['s']}): change the middle one to another type")
        for x in sc:
            d = sents[min(int(x["e"]), s1)][1] - sents[max(int(x["s"]), s0)][0]
            if d > 18:
                soft.append(f"the scene starting at sentence {x['s']} is {d:.0f} s long (max 18): split it")
        seen = {}
        for x in sc:
            for c in x.get("clips") or []:
                if c in seen:
                    soft.append(f"clip {c} is used twice (sentences {seen[c]} and {x['s']}): never reuse an id")
                seen.setdefault(c, x["s"])
    except (KeyError, ValueError, TypeError, IndexError):
        hard.append("scenes without valid s/e")
    return hard, soft[:8]


def fast_chunk(p, sents, s0, s1):
    """One no-thinking answer (~8 s) plus at most one no-thinking repair round for rule slips; hard failures raise (caller falls back to the thinking race)."""
    r = race_fast(p, "scenes")["scenes"]
    hard, soft = lint_chunk(r, sents, s0, s1)
    if hard:
        raise RuntimeError("fast answer unusable: " + "; ".join(hard))
    if soft:
        p2 = (p + "\n\nYOUR PREVIOUS ANSWER:\n" + json.dumps({"scenes": r}, ensure_ascii=False) + "\n\nIt breaks these rules:\n- " + "\n- ".join(soft)
              + "\nReply with the full corrected JSON {\"scenes\":[...]}.")
        try:
            r2 = race_fast(p2, "scenes")["scenes"]
            h2, s2 = lint_chunk(r2, sents, s0, s1)
            print(f"   chunk {s0}-{s1}: repair round {len(soft)} -> {len(s2)} slips", flush=True)
            if not h2 and len(s2) <= len(soft):
                r = r2
        except Exception as e:
            print(f"   chunk {s0}-{s1}: repair failed ({str(e)[:60]}), keeping first answer", flush=True)
    return r


def check_fast(clips, cache, rounds=2):
    """Visual check (watermark/logo/news graphic) of the plan's clips: 4 clips per no-thinking Flash-low request (JPEG tiles), 6 requests in parallel, answers cached
    under the same key clip_check uses. Clips not answered stay for the old per-clip check. (Old: 1 thinking request per clip, 75 s waits x 5 rounds.)"""
    import base64, requests
    import cf_common as CF
    sys.path.insert(0, r"C:\Users\meteh\SkullStudio\pipeline")
    import common
    todo = [c for c in clips if not CF._cfile(c, cache).exists()]

    def one(group):
        content = [{"type": "text", "text": CF.BATCH_Q}]; ids = {}
        for k, c in enumerate(group, 1):
            jpg = CF._tile_jpg(c)
            if jpg:
                ids[k] = c
                content += [{"type": "text", "text": f"CLIP {k}"}, {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(jpg).decode()}}]
        if not ids:
            return 0
        r = requests.post(common.F["base_url"].rstrip("/") + "/chat/completions", headers={"Authorization": "Bearer " + common.F["api_key"]},
                          json={"model": "ag/gemini-3.8-flash-low", "messages": [{"role": "user", "content": content}], "stream": False, "reasoning_effort": FAST_EFFORT},
                          timeout=(15, FAST_TO))
        if r.status_code != 200:
            raise RuntimeError(f"http {r.status_code}")
        ans = jparse(r.json()["choices"][0]["message"]["content"])
        n = 0
        for key, v in (ans.items() if isinstance(ans, dict) else []):
            m = re.search(r"\d+", str(key))
            if m and int(m.group()) in ids and CF._valid_one(v):
                CF.jsave(CF._cfile(ids[int(m.group())], cache), CF._verdict(v)); n += 1
        return n
    for _ in range(rounds):
        todo = [c for c in todo if not CF._cfile(c, cache).exists()]
        if not todo:
            break
        groups = [todo[i:i + 4] for i in range(0, len(todo), 4)]
        with ThreadPoolExecutor(min(6, len(groups))) as ex:
            for f in [ex.submit(one, g) for g in groups]:
                try:
                    f.result()
                except Exception as e:
                    print(f"   fast check batch failed: {str(e)[:70]}", flush=True)


def plan_cached(film, p, fn):
    """Cache by sha1(prompt + mode): a rerun/resume with unchanged inputs costs no LLM call. SF_PLAN_NOCACHE=1 skips it."""
    import hashlib
    f = W(film) / "plan_cache" / (hashlib.sha1((p + "|" + str(FAST)).encode("utf8")).hexdigest()[:20] + ".json")
    if f.exists() and not os.environ.get("SF_PLAN_NOCACHE"):
        try:
            return jload(f)
        except Exception:
            pass
    r = fn()
    if r:
        f.parent.mkdir(parents=True, exist_ok=True); jsave(f, r)
    return r


def num_ok(v, allowed):
    if v in (None, ""):
        return True
    for tok in re.findall(r"\d[\d,.:]*", str(v)):
        if tok.strip(".,") not in allowed:
            return False
    return True


def allowed_numbers(F, sents):
    from num2words import num2words
    txt = F["script"] + "\n" + F["fact"]
    ok = {t.strip(".,") for t in re.findall(r"\d[\d,.:]*", txt)}
    ok |= {t.replace(",", "") for t in ok}
    narr = " ".join(t for _, _, t in sents).lower().replace("-", " ")
    for n in range(0, 3000):
        w = num2words(n).replace("-", " ").replace(",", "")
        if re.search(rf"\b{re.escape(w)}\b", narr):
            ok.add(str(n))
    for y in range(1800, 2100):
        if num2words(y, to="year").replace("-", " ") in narr:
            ok.add(str(y))
    return ok


def validate(raw, sents, s0, s1, cat, used, allowed):
    sc = []
    for x in raw:
        try:
            x["s"], x["e"] = int(x["s"]), int(x["e"])
        except (KeyError, ValueError, TypeError):
            continue
        if x.get("type") not in S.TYPES or x["type"] == "endcard":
            x["type"] = "statement"
        sc.append(x)
    sc = sorted([x for x in sc if s0 <= x["s"] <= s1], key=lambda x: x["s"])
    out, nxt = [], s0
    for x in sc:                                         # contiguous cover, no overlap
        if x["e"] < nxt:
            continue
        x["s"] = nxt if not out or x["s"] > nxt else max(x["s"], nxt)
        if x["s"] > nxt and out:
            out[-1]["e"] = x["s"] - 1
        x["s"] = max(x["s"], nxt); x["e"] = min(max(x["e"], x["s"]), s1)
        out.append(x); nxt = x["e"] + 1
    if not out:
        out = [dict(s=s0, e=s1, type="full", clips=[])]
    out[0]["s"] = s0; out[-1]["e"] = s1
    for x in out:
        t = x["type"]
        for f in ("number", "label", "sub", "line", "time", "title", "text"):
            if not num_ok(x.get(f), allowed):
                print(f"   drop unsupported number in {t}.{f}: {x.get(f)!r}", flush=True)
                if t in ("number", "print_number") and f == "number":
                    x["type"] = t = "print" if t == "print_number" else "statement"
                    x["text"] = x.get("label") or ""
                x[f] = ""
        if t == "document":
            x["lines"] = [l for l in x.get("lines") or [] if isinstance(l, list) and len(l) == 2 and num_ok(l[1], allowed) and num_ok(l[0], allowed)]
            if not x["lines"]:
                x["type"] = t = "print"
        if t == "compare":
            x["items"] = [it for it in x.get("items") or [] if isinstance(it, list) and len(it) >= 2 and num_ok(it[1], allowed) and num_ok(it[-1], allowed)]
            if len(x["items"]) < 2:
                x["type"] = t = "print"
        if t == "statement" and not (x.get("text") or "").strip():
            x["type"] = t = "full"
        if t in S.NEEDS_CLIPS:
            ids = [c for c in (x.get("clips") or []) if c in cat and c not in used and not (cat[c]["img"] and t in ("full", "monitor"))]
            ids = [c for c in ids if not (cat[c]["kind"] == "3D" and t != "monitor")]
            mid = (sents[x["s"]][0] + sents[x["e"]][1]) / 2
            need = 2 if (t in ("full", "print") and sents[x["e"]][1] - sents[x["s"]][0] > 8 and x["e"] > x["s"]) else 1
            while len(ids) < need:
                pool = [c for c in cat.values() if c["id"] not in used and c["id"] not in ids and (c["kind"] != "3D" or t == "monitor")
                        and not (c["img"] and t in ("full", "monitor"))]
                if not pool:
                    break
                ids.append(min(pool, key=lambda c: abs(c["t"] - mid) + (0 if c["kind"] == "FOOTAGE" else 25))["id"])
            if not ids:
                x["type"], x["text"] = "statement", x.get("kicker") or x.get("line") or ""
                if not x["text"]:
                    x["type"], x["text"] = "statement", "· · ·"
            x["clips"] = ids[:2]; used.update(ids[:2])
    return out


def cmd_plan(film):
    work = W(film); work.mkdir(parents=True, exist_ok=True)
    F = load_film(film); sents = F["sents"]
    cfw = HERE.parent / "casefile" / "work" / film
    base = cfw if cfw.exists() else work
    cat = catalog(F, base / "clipcheck", base / "flow")
    print(f"{film}: {len(sents)} sentences, {F['total']:.1f}s, catalog {len(cat)} clips ({sum(c['kind']=='ENGRAVING' for c in cat.values())} engraving)", flush=True)
    sec_f = work / "sections.json"
    secs = jload(sec_f) if sec_f.exists() else plan_sections(F, sents); jsave(sec_f, secs)
    print("  sections:", [(x["s"], x["kicker"], x.get("title")) for x in secs], flush=True)
    bounds = [int(x["s"]) for x in secs] + [len(sents)]
    jobs = []
    for k, sec in enumerate(secs):                         # long sections planned in ~45-sentence pieces
        a, b = bounds[k], bounds[k + 1] - 1
        n = max(1, math.ceil((b - a + 1) / 40))
        for j in range(n):
            pa = a + j * (b - a + 1) // n; pb = a + (j + 1) * (b - a + 1) // n - 1
            jobs.append((pa, pb, sec if j == 0 else dict(sec, kicker=sec["kicker"] + " (continued, no title scene)")))
    raw_f = work / "plan_raw.json"
    raw = jload(raw_f) if raw_f.exists() else {}
    todo = [j for j in jobs if f"{j[0]}-{j[1]}" not in raw]
    with ThreadPoolExecutor(max(1, min(len(todo), 9 if FAST else 6))) as ex:   # all chunks at once (no-thinking Flash: 9 in parallel answered in 8 s wall)
        for j, r in zip(todo, ex.map(lambda j: plan_chunk(F, sents, j[0], j[1], j[2], cat), todo)):
            raw[f"{j[0]}-{j[1]}"] = r; jsave(raw_f, raw); print(f"  planned {j[0]}-{j[1]}: {len(r)} scenes", flush=True)
    allowed = allowed_numbers(F, sents); used = set(); scenes = []
    for pa, pb, sec in jobs:
        scenes += validate(raw[f"{pa}-{pb}"], sents, pa, pb, cat, used, allowed)
    # visual check (watermark/logo/news graphic) only for the clips the plan uses; bad ones swap to the nearest clean unused clip
    cache = base / "clipcheck"; verdict = {}
    def chk(cid):
        if cid not in verdict:
            c = cat[cid]
            v = dict(bad=False, side=None) if c["kind"] == "ENGRAVING" else dict(clip_check(c["src"], cache))
            if v.get("unverified"): v = dict(bad=True, side=None)
            if v["bad"] and not v.get("side") and not v.get("text_card"):
                v["rect"] = safe_rect(v.get("marks") or [])
            verdict.setdefault(cid, v)
        return verdict[cid]
    for rnd in range(5):
        ids = sorted({c for x in scenes for c in x.get("clips") or []})
        if FAST and os.environ.get("SF_CHECK_FAST", "1") != "0":
            check_fast([cat[c]["src"] for c in ids if c not in verdict and cat[c]["kind"] != "ENGRAVING"], cache)
        ex = ThreadPoolExecutor(12); futs = {c: ex.submit(chk, c) for c in ids if c not in verdict}
        from concurrent.futures import wait as fwait
        fwait(list(futs.values()), timeout=75)
        pending = set()
        for c, f in futs.items():
            if not f.done():
                if rnd < 3:                                 # slow Flash: keep the clip, its answer is cached when it lands; ask again next round
                    pending.add(c); continue
                verdict[c] = dict(bad=True, side=None)      # still hung after 4 rounds: unverified clip is not used
                print(f"   {c}: check timed out, replacing", flush=True)
            elif f.exception():
                verdict[c] = dict(bad=True, side=None)
        ex.shutdown(wait=False, cancel_futures=True)
        def unusable(c, t):
            v = verdict.get(c)
            return bool(v and v["bad"] and not v.get("side") and not (v.get("rect") and t != "full"))
        bad = sorted({c for x in scenes for c in x.get("clips") or [] if unusable(c, x["type"])})
        for c in ids:
            v = verdict.get(c) or {}
            cat[c]["crop"] = v.get("side"); cat[c]["rect"] = v.get("rect") if not v.get("side") else None
        print(f"  visual check round {rnd}: {len(ids)} clips, {len(bad)} to replace" + (f", {len(pending)} slow (asked again)" if pending else ""), flush=True)
        if not bad and not pending:
            break
        cand = [c for c in cat.values() if c["id"] not in used]
        for x in scenes:
            for k, c in enumerate(x.get("clips") or []):
                if c in bad and unusable(c, x["type"]):
                    pool = [q for q in cand if q["id"] not in used and not unusable(q["id"], x["type"]) and (q["kind"] != "3D" or x["type"] == "monitor") and not (q["img"] and x["type"] in ("full", "monitor"))]
                    if pool:
                        q = min(pool, key=lambda q: abs(q["t"] - cat[c]["t"]) + (0 if q["kind"] == cat[c]["kind"] else 20))
                        x["clips"][k] = q["id"]; used.add(q["id"])
            x["clips"] = [c for c in x.get("clips") or [] if c not in bad]
            if x["type"] in S.NEEDS_CLIPS and not x["clips"]:
                x["lost"] = x["type"]; x["type"], x["text"] = "statement", x.get("kicker") or "· · ·"
    # reuse: a scene that lost every clip takes a verified clean clip again (another part of it, >= 90 s from its other uses), not a text card
    times = {}
    for x in scenes:
        for c in x.get("clips") or []:
            times.setdefault(c, []).append(sents[x["s"]][0])
    n_re = 0
    for x in scenes:
        t = x.pop("lost", None)
        if not t:
            continue
        at = sents[x["s"]][0]
        pool = [c for c, v in verdict.items() if (not v["bad"] or v.get("side") or (v.get("rect") and t != "full"))
                and not (cat[c]["img"] and t in ("full", "monitor")) and (cat[c]["kind"] != "3D" or t == "monitor")
                and all(abs(at - q) >= 90 for q in times.get(c, []))]
        if not pool:
            continue
        c = min(pool, key=lambda c: (len(times.get(c, [])), abs(cat[c]["t"] - at)))
        x["type"], x["clips"], x["var"] = t, [c], [len(times.get(c, []))]; times.setdefault(c, []).append(at); n_re += 1
    if n_re:
        print(f"  {n_re} clip-less scenes reuse a clean clip (another part of it)", flush=True)
    used = {c for x in scenes for c in x.get("clips") or []}
    # timing: scene = its first sentence start .. next scene start
    for k, x in enumerate(scenes):
        x["a"] = 0.0 if k == 0 else round(sents[x["s"]][0] - .15, 3)
    for k, x in enumerate(scenes):
        b = scenes[k + 1]["a"] if k + 1 < len(scenes) else F["total"] + .4
        x["d"] = round(b - x["a"], 3)
        x["beats"] = [round(max(0, sents[i][0] - x["a"]), 3) for i in range(x["s"], x["e"] + 1)]
        x["narr"] = " ".join(sents[i][2] for i in range(x["s"], x["e"] + 1))
    scenes.append(dict(type="endcard", s=len(sents), e=len(sents), a=round(F["total"] + .4, 3), d=END_CARD, beats=[0], clips=[]))
    from collections import Counter
    print("  types:", dict(Counter(x["type"] for x in scenes)), " clips used:", len(used), flush=True)
    jsave(work / "plan.json", dict(film=film, title=F["title"], label=case_label(film, F["script"]), total=F["total"], scenes=scenes,
                                   catalog={k: v for k, v in cat.items() if k in used}))


# -------------------------------------------------------------------------------------------- prep
def probe_dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout.strip()
    try:
        return float(r)
    except ValueError:
        return 0.0


CROP = {"top": "crop=iw:ih*0.86:0:ih*0.14", "bottom": "crop=iw:ih*0.86:0:0", "left": "crop=iw*0.86:ih:iw*0.14:0", "right": "crop=iw*0.86:ih:0:0"}


def clip_uses(scenes):
    """(clip id, needed seconds, size) for every clip slot, mirroring sf_scenes timing"""
    out = []
    for k, x in enumerate(scenes):
        t, d, ids = x["type"], x["d"], x.get("clips") or []
        if t not in S.NEEDS_CLIPS or not ids:
            continue
        vv = x.get("var") or []
        if vv and vv[0]:
            out.append((ids[0], d, t == "full", vv[0]))
            continue
        big = t == "full"
        if t == "full" and len(ids) > 1:
            cut = S.beat(x["beats"], 1, d, 0) if len(x["beats"]) > 1 else d
            if cut < 2.5 or d - cut < 2.5:
                cut = d / 2 if d >= 6 else d
            out += [(ids[0], cut, big, 0), (ids[1], d - cut, big, 0)] if cut < d else [(ids[0], d, big, 0)]
        elif t == "print" and len(ids) > 1:
            t2 = S.beat(x["beats"], 1, d, 0) if len(x["beats"]) > 1 else d / 2
            t2 = min(max(t2, 2.2), d - 2.2)
            out += [(ids[0], d, False, 0), (ids[1], d - t2, False, 0)]
        else:
            out.append((ids[0], d, big, 0))
    return out


def bars_crop(c):
    """flow clips: 6% centre crop (thin paper frame); footage/photos: crop uniform edge bars (pillarbox/letterbox, any colour)"""
    if c["kind"] == "ENGRAVING":
        return ["crop=iw*0.94:ih*0.94"]
    import numpy as np
    ss = [] if c["img"] else ["-ss", f"{max(0.0, probe_dur(c['src']) * .4):.2f}"]
    r = subprocess.run(["ffmpeg", "-v", "error", *ss, "-i", c["src"], "-frames:v", "1", "-vf", "scale=320:180,format=gray", "-f", "rawvideo", "-"], capture_output=True)
    if len(r.stdout) != 320 * 180:
        return []
    a = np.frombuffer(r.stdout, np.uint8).reshape(180, 320).astype(float)
    def run(lines):
        n = 0
        for ln in lines:
            if ln.std() < 5: n += 1
            else: break
        return n
    L, R, T, B = run(a.T), run(a.T[::-1]), run(a), run(a[::-1])
    L, R, T, B = [v if v >= 4 else 0 for v in (L, R, T, B)]
    if not (L or R or T or B) or L + R > 160 or T + B > 90:
        return []
    L, R, T, B = [v + 2 if v else 0 for v in (L, R, T, B)]
    return [f"crop=iw*{(320-L-R)/320:.4f}:ih*{(180-T-B)/180:.4f}:iw*{L/320:.4f}:ih*{T/180:.4f}"]


def clip_name(cid, need, big, var=0):
    return f"{cid}_{need:.2f}_{'b' if big else 's'}{f'_v{var}' if var else ''}.mp4"


def prep_one(c, need, big, dst, var=0):
    if dst.exists():
        return
    need = max(need, .5) + .3
    w, h = (1920, 1080) if big else (1280, 720)
    rc = c.get("rect")
    vf = ([CROP[c["crop"]]] if c.get("crop") else [f"crop=iw*{rc[2]}:ih*{rc[2]}:iw*{rc[0]}:ih*{rc[1]}"] if rc else bars_crop(c)) + [f"scale={w}:{h}:force_original_aspect_ratio=increase", f"crop={w}:{h}", "setsar=1"]
    if c["img"]:
        z = f"zoompan=z='1+0.0009*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(need*FPS)+2}:s={w}x{h}:fps={FPS}"
        args = ["-loop", "1", "-i", c["src"], "-vf", ",".join(vf[:-1] + [f"scale={w*2}:{h*2}", z]), "-t", f"{need:.2f}"]
    else:
        L = probe_dur(c["src"]) or need
        if L >= need:
            ss = max(0, min(L - need, L * .08)) if not var else (L * .08 + var * L * .37) % max(.01, L - need)
            args = ["-ss", f"{ss:.2f}", "-i", c["src"], "-t", f"{need:.2f}", "-vf", ",".join(vf + [f"fps={FPS}"])]
        elif L * 1.6 >= need:
            args = ["-i", c["src"], "-vf", ",".join(vf + [f"setpts={need/L:.4f}*PTS", f"fps={FPS}"]), "-t", f"{need:.2f}"]
        else:
            args = ["-stream_loop", "-1", "-i", c["src"], "-vf", ",".join(vf + [f"setpts={1.5:.2f}*PTS", f"fps={FPS}"]), "-t", f"{need:.2f}"]
    ffmpeg([*args, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-g", "25", str(dst)])


def cmd_prep(film, rng=None):
    work = W(film); P = jload(work / "plan.json"); cat = P["catalog"]
    scenes = [x for x in P["scenes"] if not rng or (x["a"] < rng[1] and x["a"] + x["d"] > rng[0])]
    cdir = work / "assets" / "clips"; cdir.mkdir(parents=True, exist_ok=True)
    for sub in ("fonts", "img"):
        if not (work / "assets" / sub).exists():
            shutil.copytree(SAMPLE / sub, work / "assets" / sub)
    jobs = []
    for cid, need, big, var in clip_uses(scenes):
        jobs.append((cat[cid], need, big, cdir / clip_name(cid, need, big, var), var))
    t = time.time()
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(lambda j: prep_one(*j), jobs))
    print(f"  prepped {len(jobs)} clips in {time.time()-t:.0f}s", flush=True)


# -------------------------------------------------------------------------------------------- build
def chrome_comp(label, d):
    return f'''<template>
<style>{S.FONTS}
#root{{position:absolute;inset:0;pointer-events:none}}
.c{{position:absolute;width:46px;height:46px;border-color:rgba(232,226,211,.55);border-style:solid;border-width:0}}
</style>
<div id="root" data-composition-id="chrome" data-width="1920" data-height="1080" data-layout-allow-overlap>
 <div class="c" style="left:60px;top:60px;border-left-width:2px;border-top-width:2px"></div>
 <div class="c" style="right:60px;top:60px;border-right-width:2px;border-top-width:2px"></div>
 <div class="c" style="left:60px;bottom:60px;border-left-width:2px;border-bottom-width:2px"></div>
 <div class="c" style="right:60px;bottom:60px;border-right-width:2px;border-bottom-width:2px"></div>
 <div style="position:absolute;left:84px;top:76px;font-family:WBahn;font-size:17px;letter-spacing:.3em;color:rgba(232,226,211,.62)">
   <span id="recdot" style="display:inline-block;width:11px;height:11px;border-radius:50%;background:{S.RED};margin-right:12px;vertical-align:1px"></span>{S.e(label)}</div>
 <div style="position:absolute;right:84px;top:72px;font-family:WGaramond;font-size:24px;letter-spacing:.38em;color:rgba(232,226,211,.38)">WRATH OF EARTH</div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
tl.fromTo("#recdot", {{opacity: 1}}, {{opacity: 0.15, duration: 0.5, ease: "none", repeat: {max(1, int(d*2)-2)}, yoyo: true}}, 0.3);
window.__timelines["chrome"] = tl;
</script>
</template>
'''


def index_html(hosts, total, chrome_d):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{S.FONTS}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{S.INK}}}
#root{{position:relative;width:1920px;height:1080px;overflow:hidden}}
#bgfill{{position:absolute;inset:0;background:{S.INK}}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="1920" data-height="1080">
<div id="bgfill"></div>
{hosts}
{f'<div id="chrome" data-composition-id="chrome" data-composition-src="compositions/chrome.html" data-start="0" data-duration="{chrome_d:.3f}" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:20"></div>' if chrome_d > 0 else ''}
</div>
<script>const tl = gsap.timeline({{ paused: true }}); window.__timelines["main"] = tl;</script>
</body></html>
'''


def chunks_of(scenes, rng=None):
    if rng:
        sel = [x for x in scenes if x["a"] < rng[1] and x["a"] + x["d"] > rng[0]]
        return [sel]
    out, cur, c0 = [], [], 0.0
    for x in scenes:
        if cur and x["a"] - c0 >= CHUNK:
            out.append(cur); cur, c0 = [], x["a"]
        cur.append(x)
    out.append(cur)
    return out


def cmd_build(film, rng=None):
    work = W(film); P = jload(work / "plan.json"); scenes = P["scenes"]
    cdir = "assets/clips"
    events, comps = [], {}
    secs = jload(work / "sections.json") if (work / "sections.json").exists() else []
    starts = [int(q["s"]) for q in secs]
    n_pr = 0
    for x in scenes:                                       # Vox collage: every other evidence print after the hook (V2 edit: COLLAGE/PRINT modes)
        si = max([k for k, v in enumerate(starts) if v <= x["s"]] or [0])
        x["mode"] = ""
        if x["type"] == "print" and si > 0:
            n_pr += 1; x["mode"] = "collage" if n_pr % 2 == 0 else ""
    for k, x in enumerate(scenes):
        sid = f"s{k:03d}"; x["sid"] = sid
        names = []
        uses = clip_uses([x])
        for cid, need, big, var in uses:
            names.append(f"{cdir}/{clip_name(cid, need, big, var)}")
        if x["type"] == "print" and len(names) == 2:
            pass
        comp, ev = S.render_scene(sid, x, names)
        comps[sid] = comp; events += ev
    jsave(work / "events.json", events); jsave(work / "plan.json", P)
    parts = chunks_of(scenes, rng)
    dirs = []
    for n, part in enumerate(parts):
        d = work / (f"hf_test" if rng else f"hf_{n:02d}")
        (d / "compositions").mkdir(parents=True, exist_ok=True)
        if not (d / "assets").exists():
            subprocess.run(["cmd", "/c", "mklink", "/J", str(d / "assets"), str(work / "assets")], capture_output=True)
        c0 = part[0]["a"]; c1 = part[-1]["a"] + part[-1]["d"]
        hosts = []
        for x in part:
            (d / "compositions" / f'{x["sid"]}.html').write_text(comps[x["sid"]], encoding="utf8")
            hosts.append(f'<div id="{x["sid"]}" data-composition-id="{x["sid"]}" data-composition-src="compositions/{x["sid"]}.html" data-start="{x["a"]-c0:.3f}" '
                         f'data-duration="{x["d"]:.3f}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:1"></div>')
        chrome_end = min(c1, P["total"] + .4) - c0
        (d / "compositions" / "chrome.html").write_text(chrome_comp(P["label"], chrome_end), encoding="utf8")
        (d / "index.html").write_text(index_html("\n".join(hosts), c1 - c0, chrome_end), encoding="utf8")
        for f, src in (("hyperframes.json", SAMPLE.parent / "hyperframes.json"), ("package.json", SAMPLE.parent / "package.json")):
            if not (d / f).exists():
                shutil.copy(src, d / f)
        jsave(d / "chunk.json", dict(a=c0, b=c1, scenes=[x["sid"] for x in part]))
        dirs.append(d)
    print(f"  built {len(scenes)} scenes in {len(dirs)} chunk(s)", flush=True)
    return dirs


# -------------------------------------------------------------------------------------------- render + mix
import threading as _th
_ADMIT = {"lock": _th.Lock(), "starts": []}
CHUNK_PEAK_GB = float(os.environ.get("SF_CHUNK_PEAK_GB", "2.3"))    # speed_1106/render: peak RSS 2.2 GB per chunk (-w 3 --gpu --no-browser-gpu)
CHUNK_RESERVE_GB = float(os.environ.get("SF_RENDER_RESERVE_GB", "0.7"))   # left to the desktop (resources.CRITICAL_MB)
CHUNK_RAMP_S = 25                                                         # Chrome + encoder reach their peak this long after start


def admit_chunk(timeout=1800):
    """Wait until one more chunk fits in the memory that is free NOW, minus what chunks started in the last
    CHUNK_RAMP_S seconds are still going to take. wait_ram(3.0) checked the free memory only, so two chunks
    started together both saw 3+ GB and together took 4.7-5.9 GB (par 2, default GPU: aborted at 0.65 GB free).
    The first chunk of this process always runs once the free memory clears the old 3.0 GB line."""
    t0 = time.time()
    while True:
        with _ADMIT["lock"]:
            now = time.time()
            _ADMIT["starts"] = [t for t in _ADMIT["starts"] if now - t < CHUNK_RAMP_S]
            pending = len(_ADMIT["starts"]) * CHUNK_PEAK_GB
            if free_gb() - pending >= CHUNK_PEAK_GB + CHUNK_RESERVE_GB:
                _ADMIT["starts"].append(now)
                return
        if time.time() - t0 > timeout:
            raise RuntimeError("no room for a render chunk after %d s" % timeout)
        time.sleep(5)


def render_dir(d, out=None):
    final = d / "out.mp4"
    if final.exists() and final.stat().st_size > 1e5:
        return final
    out = out or final
    admit_chunk()
    t = time.time()
    log = open(d / "render.log", "w", encoding="utf8")
    import os, shutil
    env = dict(os.environ)
    shim = Path("C:/Users/meteh/Kanallar/bin/hf_ffmpeg_shim.exe")     # caps HyperFrames' libx264 at 4 threads: 890 -> 460 MB per encode
    if shim.is_file() and shutil.which("ffmpeg") and "HYPERFRAMES_FFMPEG_PATH" not in env:
        env.update(HF_REAL_FFMPEG=shutil.which("ffmpeg"), HF_X264_THREADS="4", HYPERFRAMES_FFMPEG_PATH=str(shim))
    base = f'npx --yes {HF} render "{d}" -o "{out}" -f {FPS} --crf 18 -w 3 --quiet'
    # --gpu: NVENC for the intermediate encode; --no-browser-gpu: ~0.8 GB less RAM per render (speed_1106/render: par 2 123->93 s, SSIM at noise floor)
    r = subprocess.run(base + " --gpu --no-browser-gpu", shell=True, stdout=log, stderr=subprocess.STDOUT, env=env)
    if r.returncode or not out.exists():
        log.write("\n== gpu render failed, retrying without --gpu\n"); log.flush()
        r = subprocess.run(base, shell=True, stdout=log, stderr=subprocess.STDOUT, env=env)
    log.close()
    if r.returncode or not out.exists():
        raise RuntimeError(f"render failed {d}: see {d/'render.log'}")
    print(f"  rendered {d.name} in {time.time()-t:.0f}s", flush=True)
    return out


REMOTE = ["a1", "vds"]     # extra render hosts (tools/remote_render.py); --local-only turns them off
RATE = {"local": 0.40, "a1": 0.10, "vds": 0.12}   # video-s per wall-s per slot (RTEST 6x24 s, 2026-11-06); local is re-measured live


def _remote_slots(hosts):
    """[(host name, host cfg, workers per render)] per parallel slot, only for hosts that answer ssh now."""
    sys.path.insert(0, str(HERE.parent / "tools"))
    import remote_render as R
    slots = []
    for h in hosts:
        cfg = R.HOSTS[h]
        if R.ssh(cfg, "true", timeout=25).returncode == 0:
            slots += [(h, cfg, cfg["w"])] * cfg["par"]
        else:
            print(f"  render host {h} unreachable, skipped", flush=True)
    return R, slots


def cmd_render(film, rng=None, par=2, remote=None):
    """Work-stealing render: `par` local slots + remote slots (a1 3x, vds 1x) pull chunks from one queue.
    Measured (testbench/offload_1106/ORACLE_REPORT.md): ARM/x86 output identical (SSIM 0.989); a remote slot is
    ~2x slower per chunk than a local one, so a remote slot only takes a chunk the local slots would not reach
    before it finishes. A remote failure gives the chunk back to the local slots. An idle local slot re-renders
    a remote chunk (to out_spec.mp4) only when the remote is expected to need clearly longer; first file wins."""
    work = W(film)
    dirs = [work / "hf_test"] if rng else sorted(p for p in work.glob("hf_[0-9][0-9]"))
    hosts = REMOTE if remote is None else remote
    if rng or not hosts:
        with ThreadPoolExecutor(par) as ex:
            return list(ex.map(render_dir, dirs))
    import threading
    R, slots = _remote_slots(hosts)
    lock = threading.Lock()
    todo = [d for d in dirs if not R.out_ok(d)]
    local_only, remote_busy, done, spec, lrate = [], {}, set(), set(), []
    dur = lambda d: R.expect_dur(d)

    def ok(d):
        return d.name in done or R.out_ok(d)

    def local_rate():
        return sum(lrate[-4:]) / len(lrate[-4:]) if lrate else RATE["local"]

    def take_local():
        with lock:
            if local_only:
                return local_only.pop(0), False
            if todo:
                return todo.pop(0), False
            now = time.time()
            for d, (t0, h) in sorted(remote_busy.items(), key=lambda kv: kv[1][0]):
                left = t0 + dur(d) / RATE[h] - now
                overdue = now - t0 > 1.5 * dur(d) / RATE[h]          # remote far behind its rate (overloaded host): take it
                if d.name not in spec and not ok(d) and (left > 1.3 * dur(d) / local_rate() or overdue):
                    spec.add(d.name); return d, True
        return None, False

    def run_local(d, out=None):
        t = time.time(); render_dir(d, out)
        lrate.append(dur(d) / max(time.time() - t, 1))

    def local_worker():
        while True:
            d, speculative = take_local()
            if d is None:
                with lock:
                    if not todo and not local_only and all(ok(x) for x in remote_busy):
                        return
                time.sleep(5); continue
            if not speculative:
                run_local(d); done.add(d.name); continue
            tmp = d / "out_spec.mp4"
            try:
                run_local(d, tmp)
                with lock:
                    if not ok(d):
                        os.replace(tmp, d / "out.mp4"); done.add(d.name)
                        print(f"  {d.name}: local copy finished first", flush=True)
            except Exception as e:
                print(f"  {d.name}: speculative render failed: {str(e)[:150]}", flush=True)
            finally:
                tmp.unlink(missing_ok=True)

    def remote_worker(h, cfg, w):
        while True:
            with lock:
                # local slots would reach the k-th queued chunk after ~ (k // par) local chunk-times;
                # take the last chunk only if this slot finishes it sooner than that
                if not todo:
                    return
                if par == 0:                       # --remote-only: another film holds this PC's render slot
                    d = todo.pop(0)
                else:
                    d = todo[-1]
                    local_wait = (len(todo) - 1) // par * dur(d) / local_rate() + dur(d) / local_rate()
                    if dur(d) / RATE[h] >= local_wait:
                        return
                    todo.pop()
                remote_busy[d] = (time.time(), h)
            try:
                if ok(d):
                    continue
                R.do_chunk(work, d.name, cfg, w)
                done.add(d.name); print(f"  rendered {d.name} on {h}", flush=True)
            except Exception as e:
                print(f"  {d.name} failed on {h}, back to local: {str(e)[:200]}", flush=True)
                with lock:
                    if not ok(d):
                        local_only.append(d)
                return                             # one failure takes this slot out
            finally:
                with lock:
                    remote_busy.pop(d, None)

    print(f"  render: {len(todo)} chunks, {par} local + {len(slots)} remote slots", flush=True)
    th = [threading.Thread(target=remote_worker, args=sl, daemon=True) for sl in slots]
    th += [threading.Thread(target=local_worker, daemon=True) for _ in range(par)]
    for t in th:
        t.start()
    for t in th:
        t.join()
    bad = [d.name for d in dirs if not ok(d)]
    if bad:
        raise RuntimeError(f"render incomplete: {bad}")
    return [d / "out.mp4" for d in dirs]


NVENC = True     # user approved 2026-11-06; --x264 forces the old encoder
NVENC_ARGS = ["-preset", "p6", "-tune", "hq", "-rc", "vbr", "-b:v", "5M", "-maxrate", "7M", "-bufsize", "14M",
              "-spatial-aq", "1", "-temporal-aq", "1"]


def cmd_mix(film, rng=None):
    work = W(film); P = jload(work / "plan.json")
    F = load_film(film)
    vn = A.voice_norm(F["voice"], work / "voice_n16.wav")
    events = [tuple(e) for e in jload(work / "events.json")]
    sec_idx, items = 0, []
    secs = [int(s["s"]) for s in jload(work / "sections.json")]
    for x in P["scenes"]:
        while sec_idx + 1 < len(secs) and x["s"] >= secs[sec_idx + 1]:
            sec_idx += 1
        items.append(dict(sec=sec_idx, a=x["a"], b=x["a"] + x["d"], kind="memorial" if x["type"] == "memorial" else ""))
    if rng:
        chunk = jload(work / "hf_test" / "chunk.json"); t0, t1 = chunk["a"], chunk["b"]
        aud = work / "_audio_test.wav"; A.build(items, events, t0, t1, vn, aud, work)
        vids = [work / "hf_test" / "out.mp4"]; final = work / f"TEST_{int(t0)}-{int(t1)}.mp4"
    else:
        t0, t1 = 0.0, P["total"] + .4 + END_CARD
        aud = work / "_audio_full.wav"
        if not aud.exists():
            A.build(items, events, t0, t1, vn, aud, work)
        vids = sorted(work.glob("hf_[0-9][0-9]/out.mp4"))
        dd = DELIVERY / film; dd.mkdir(parents=True, exist_ok=True)
        final = dd / f"{film}_WRATH_OF_EARTH_V3.mp4"
    lst = work / "_concat.txt"
    lst.write_text("".join(f"file '{v.as_posix()}'\n" for v in vids), encoding="utf8")
    head = ["-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(aud), "-map", "0:v", "-map", "1:a",
            "-vf", "noise=alls=4:allf=t,format=yuv420p"]
    tail = ["-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", str(final)]
    x264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-threads", "4"]
    if NVENC:
        try:            # 17x faster than x264 medium, half the size, same SSIM/PSNR (testbench/offload_1106/local)
            ffmpeg([*head, "-c:v", "h264_nvenc", *NVENC_ARGS, *tail])
        except Exception as e:      # GPU busy / no session: never stop the film, fall back to x264
            print("  nvenc failed, x264 fallback:", str(e)[:200], flush=True)
            ffmpeg([*head, *x264, *tail])
    else:
        ffmpeg([*head, *x264, *tail])
    print("  final:", final, f"{final.stat().st_size/1e6:.0f} MB", flush=True)
    return final


def sheet(video, out, n=24):
    from PIL import Image
    import io
    L = probe_dur(video); ims = []
    for k in range(n):
        t = L * (k + .5) / n
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf", "scale=480:270", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if p.stdout:
            ims.append(Image.open(io.BytesIO(p.stdout)).convert("RGB"))
    cols = 4; rows = math.ceil(len(ims) / cols)
    sh = Image.new("RGB", (480 * cols, 270 * rows))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % cols) * 480, (k // cols) * 270))
    sh.save(out, quality=85)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("film"); ap.add_argument("cmd")
    ap.add_argument("--range", nargs=2, type=float)
    ap.add_argument("--par", type=int, default=2)
    ap.add_argument("--local-only", action="store_true", help="render only on this PC (no a1/vds)")
    ap.add_argument("--remote-only", action="store_true", help="render only on a1/vds (another film holds this PC's render slot)")
    ap.add_argument("--x264", action="store_true", help="CPU libx264 for the final mix instead of NVENC")
    a = ap.parse_args()
    NVENC = not a.x264
    rng = tuple(a.range) if a.range else None
    steps = ["plan", "prep", "build", "render", "mix"] if a.cmd == "all" else [a.cmd]
    for st in steps:
        t = time.time(); print(f"== {a.film} {st}", flush=True)
        if st == "plan": cmd_plan(a.film)
        elif st == "prep": cmd_prep(a.film, rng)
        elif st == "build": cmd_build(a.film, rng)
        elif st == "render": cmd_render(a.film, rng, 0 if a.remote_only else a.par, [] if a.local_only else None)
        elif st == "mix":
            f = cmd_mix(a.film, rng); sheet(f, W(a.film) / (f.stem + "_sheet.jpg"))
        elif st == "sheet":
            pass
        print(f"== {st} done {time.time()-t:.0f}s", flush=True)
    import os; os._exit(0)      # hung check threads must not keep the process alive
