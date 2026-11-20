"""Shared bits for the Case File builder: film loading (EDL rows + sentences), LLM call, RAM gate, ffmpeg runner."""
import ctypes, json, re, subprocess, sys, threading, time, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
FPS = 25
OUTS = Path(r"C:\Users\meteh\CodexOutputs")
DELIVERY = Path(r"C:\Users\meteh\OneDrive\Desktop\Channells\ENGINEERED")
SCRIPTS = Path(r"C:\Users\meteh\Downloads\Compressed\drive-download-20261105T125326Z-1-001")
SFX = Path(r"C:\Users\meteh\.claude\skills\media-use\audio\assets\sfx")
GEMINI = r"C:\Users\meteh\.gemini\scripts"      # imported read-only (delivery helpers, ask_codex)
INK, PAPER, RED = (11, 15, 16), (232, 226, 211), (192, 38, 34)
_ff = threading.BoundedSemaphore(2)               # hard cap: 2 ffmpeg at once


def free_gb():
    class M(ctypes.Structure):
        _fields_ = [("l", ctypes.c_ulong), ("p", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in "tp ap tpf apf tv av ae".split()]
    m = M(); m.l = ctypes.sizeof(M); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ap / 2 ** 30


def wait_ram(need=2.5):
    while free_gb() < need:
        print(f"  free RAM {free_gb():.1f} GB < {need}; waiting 20 s", flush=True); time.sleep(20)


def ffmpeg(args, stdin_gen=None):
    """Run ffmpeg (libx264 only) under the 2-process cap. stdin_gen yields raw frame bytes."""
    with _ff:
        wait_ram()
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", *args], stdin=subprocess.PIPE if stdin_gen else None,
                             stderr=subprocess.PIPE)
        if stdin_gen:
            try:
                for b in stdin_gen:
                    p.stdin.write(b)
            finally:
                p.stdin.close()
        err = p.stderr.read().decode("utf8", "replace"); p.wait()
        if p.returncode:
            raise RuntimeError("ffmpeg failed: " + err[-1500:] + " :: " + " ".join(map(str, args))[:600])


def h(*a):
    return hashlib.sha1(json.dumps(a, sort_keys=True, default=str).encode()).hexdigest()[:12]


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf8"))


def jsave(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True); Path(p).write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf8")


BAD_REVIEW = re.compile(r"watermark|logo|burned.?in|on-screen text|caption|ticker|banner|lower.third|channel (name|bug)|news graphic|subtitles", re.I)


def load_film(film):
    """EDL rows (one per shot) + sentence timings + script text. Uses delivery.py helpers read-only."""
    sys.path.insert(0, GEMINI)
    from documentary_materials import delivery as D
    proj = OUTS / film; out = proj / "03_materials"
    plan = jload(out / "material_plan.json")
    rows = []
    for i, s in enumerate(plan["shots"], 1):
        rj = out / "shots" / f'{s["shot_id"]:04d}' / "result.json"
        clip, flag = None, False
        if rj.exists():
            r = jload(rj); a = r.get("artifact") or {}
            for k in ("visual_path", "path"):
                if a.get(k) and Path(a[k]).exists():
                    clip = a[k]; break
            d = (r.get("review") or {}).get("data") or {}
            flag = bool(BAD_REVIEW.search(" ".join(map(str, (d.get("issues") or []) + (d.get("blocking_defects") or []) + [d.get("summary") or ""]))))
        rows.append(dict(i=i, shot_id=s["shot_id"], start=s["frame_start"] / FPS, end=s["frame_end"] / FPS, cat=s["category"],
                         narr=s.get("narration") or "", scene=s.get("full_scene_narration") or "", clip=clip, flagged=flag, review_flag=flag, crop=None))
    try:
        sents = D._sentences(proj)
    except Exception as e:
        print("  sentences unavailable:", e); sents = []
    sd = next((d for d in SCRIPTS.glob("*") if d.is_dir() and d.name.split("_")[0] == film.split("_")[0]), None)
    script = fact = ""
    if sd:
        for f in sd.glob("*.md"):
            t = f.read_text(encoding="utf8", errors="replace")
            if "SCRIPT" in f.name.upper(): script = t
            elif "FACT" in f.name.upper(): fact = t
    title = (re.search(r'^# .*?"(.*?)"', script, re.M) or re.search(r"^# (.*)", script, re.M) or [0, film])[1] if script else film
    return dict(film=film, proj=proj, out=out, rows=rows, sents=sents, script=script, fact=fact, title=title,
                voice=proj / "master_voiceover.wav", total=rows[-1]["end"])


def llm(prompt, timeout=300):
    """GPT (gpt-6-sol, VDS :8765) with the pipeline's own fallback to ag/gemini-3.8-flash-high via 9router."""
    sys.path.insert(0, GEMINI)
    from ask_codex import ask_codex
    return ask_codex(prompt, model="gpt-6-sol", timeout=timeout)


def json_from(text):
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S) or re.search(r"(\{.*\})", text, re.S)
    return json.loads(m.group(1))


# ---------------------------------------------------------------- visual clip check (watermark / logo / news graphic / burned-in text)
CHECK_Q = ("You inspect 3 frames (stacked top to bottom) of ONE video clip that will be used as documentary B-roll. Look for ANY of: a licensing or stock "
           "watermark (e.g. 'NOT FOR RESALE', a seller/brand name, 'license this footage'), a channel or TV logo, a news bug ('LIVE', station number), "
           "a news banner/lower-third/ticker, burned-in captions or subtitles, or any other overlaid text/letters that are not part of the real scene "
           "(a street sign in the scene is fine). Also report if the clip is a text/title card or graphic with letters instead of real footage. "
           "Locate every mark with a normalized box [x0,y0,x1,y1] inside ITS frame (0..1, y downward). Reply JSON only: "
           '{"marks":[{"what":"short","box":[x0,y0,x1,y1]}],"text_card":false}')


def _tile(clip):
    from PIL import Image
    import io
    dur = 3.0
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip], capture_output=True, text=True).stdout.strip()
    try: dur = float(pr)
    except ValueError: pass
    ims = []
    for f in (.12, .5, .88):
        with _ff:
            p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{dur * f:.2f}", "-i", clip, "-frames:v", "1", "-vf", "scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2",
                                "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if p.stdout: ims.append(Image.open(io.BytesIO(p.stdout)).convert("RGB"))
    if not ims: return None
    t = Image.new("RGB", (960, 540 * len(ims)))
    for k, im in enumerate(ims): t.paste(im, (0, 540 * k))
    b = io.BytesIO(); t.save(b, "PNG"); return b.getvalue()


def strip_side(marks, maxfrac=.12):
    """(needs_replace, side): side in top/bottom/left/right when every mark sits inside one edge strip <= maxfrac (a crop of it keeps >= 1-maxfrac of the frame), else None."""
    if not marks: return False, None
    boxes = [m.get("box") for m in marks]
    if any(not (isinstance(b, list) and len(b) == 4) for b in boxes): return True, None
    for side, ok in (("top", lambda b: b[3] <= maxfrac), ("bottom", lambda b: b[1] >= 1 - maxfrac), ("left", lambda b: b[2] <= maxfrac), ("right", lambda b: b[0] >= 1 - maxfrac)):
        if all(ok(b) for b in boxes): return True, side
    return True, None


def _verdict(v):
    marks = [m for m in (v.get("marks") or []) if isinstance(m, dict)]
    rep, side = strip_side(marks); tc = bool(v.get("text_card"))
    return dict(bad=rep or tc, side=None if tc else side, marks=marks, text_card=tc)


def _cfile(clip, cache):
    st = Path(clip).stat(); return Path(cache) / f"{h(clip, st.st_size, int(st.st_mtime), CHECK_Q)}.json"


def clip_check(clip, cache):
    """Cached (path+size+mtime+question) Flash verdict for one clip: {'bad', 'side' (crop side or None), 'marks', 'text_card'}."""
    f = _cfile(clip, cache)
    if f.exists(): return jload(f)
    sys.path.insert(0, r"C:\Users\meteh\SkullStudio\pipeline")
    from common import flash
    png = _tile(clip); v = None
    if png:
        for _ in range(3):
            try: v = flash(CHECK_Q, png); break
            except Exception as e: print("  clip_check retry:", str(e)[:80]); time.sleep(5)
    if v is None: return dict(bad=False, side=None, marks=[], text_card=False, unverified=True)   # transport failure: not cached
    res = _verdict(v); jsave(f, res); return res


# ---- batched check: 4 clips per Flash-low request (JPEG tiles), hard timeout + hedge, single-clip fallback for anything missing/invalid
BATCH_N, BATCH_TIMEOUT, BATCH_HEDGE, BATCH_PAR = 4, 120, 60, 4
BATCH_Q = ("You inspect several video clips that will be used as documentary B-roll. Each clip is introduced by a line 'CLIP <id>' followed by ONE image with 3 frames of that clip "
           "stacked top to bottom. For EACH clip look for ANY of: a licensing or stock watermark (e.g. 'NOT FOR RESALE', a seller/brand name, 'license this footage'), a channel or TV logo, "
           "a news bug ('LIVE', station number), a news banner/lower-third/ticker, burned-in captions or subtitles, or any other overlaid text/letters that are not part of the real scene "
           "(a street sign in the scene is fine). Also report if the clip is a text/title card or graphic with letters instead of real footage. Locate every mark with a normalized box "
           "[x0,y0,x1,y1] inside ITS frame (0..1, y downward). Judge every clip independently. Reply JSON only, one key per clip id: "
           '{"<id>":{"marks":[{"what":"short","box":[x0,y0,x1,y1]}],"text_card":false}, ...}')


def _tile_jpg(clip):
    """3 frames stacked, 640x360 each, JPEG q80 (~100-200 KB)."""
    from PIL import Image
    import io
    dur = 3.0
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip], capture_output=True, text=True).stdout.strip()
    try: dur = float(pr)
    except ValueError: pass
    ims = []
    for f in (.12, .5, .88):
        with _ff:
            p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{dur * f:.2f}", "-i", clip, "-frames:v", "1", "-vf", "scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2",
                                "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if p.stdout: ims.append(Image.open(io.BytesIO(p.stdout)).convert("RGB"))
    if not ims: return None
    t = Image.new("RGB", (640, 360 * len(ims)))
    for k, im in enumerate(ims): t.paste(im, (0, 360 * k))
    b = io.BytesIO(); t.save(b, "JPEG", quality=80); return b.getvalue()


def _batch_request(content, timeout):
    """One raw Flash-low request; returns the parsed JSON object (raises on any failure)."""
    import requests
    sys.path.insert(0, r"C:\Users\meteh\SkullStudio\pipeline")
    import common
    F = common.F
    r = requests.post(F["base_url"].rstrip("/") + "/chat/completions", headers={"Authorization": "Bearer " + F["api_key"]},
                      json={"model": "ag/gemini-3.8-flash-low", "messages": [{"role": "user", "content": content}], "stream": False}, timeout=(15, timeout))
    if r.status_code != 200: raise RuntimeError(f"http {r.status_code}")
    raw = r.text
    if raw.lstrip().startswith("data:"):
        parts = [json.loads(l[5:]) for l in raw.splitlines() if l.startswith("data:") and l[5:].strip() not in ("", "[DONE]")]
        text = "".join((p["choices"][0].get("delta") or {}).get("content") or "" for p in parts if p.get("choices"))
    else:
        text = json.loads(raw)["choices"][0]["message"]["content"]
    return json_from(text)


def _valid_one(v):
    return isinstance(v, dict) and isinstance(v.get("marks", []), list) and ("marks" in v or "text_card" in v)


def _check_batch(clips, cache):
    """Verdicts for up to BATCH_N clips with ONE Flash-low request (hedged after BATCH_HEDGE s, hard BATCH_TIMEOUT s). Returns {clip: verdict} for the clips answered validly;
    the caller falls back to single calls for the rest (slow = asked again, never rejected)."""
    import base64
    from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
    content = [{"type": "text", "text": BATCH_Q}]; ids = {}
    for k, c in enumerate(clips, 1):
        jpg = _tile_jpg(c)
        if not jpg: continue
        ids[str(k)] = c
        content += [{"type": "text", "text": f"CLIP {k}"}, {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(jpg).decode()}}]
    if not ids: return {}
    t0 = time.time(); ex = ThreadPoolExecutor(2); futs = {ex.submit(_batch_request, content, BATCH_TIMEOUT)}; hedged = False; ans = None
    def second():
        return ex.submit(_batch_request, content, max(BATCH_TIMEOUT - (time.time() - t0), 5))
    try:
        while futs and ans is None:
            left = BATCH_TIMEOUT - (time.time() - t0)
            if left <= 0: break
            wait_for = left if hedged else min(left, max(BATCH_HEDGE - (time.time() - t0), 0.01))
            done, futs = wait(futs, timeout=wait_for, return_when=FIRST_COMPLETED)
            for f in done:
                try:
                    a = f.result()
                    if isinstance(a, dict) and any(_valid_one(a.get(i)) for i in ids): ans = a; break
                except Exception as e: print("  batch check error:", str(e)[:80])
            if ans is None and not hedged and (not futs or time.time() - t0 >= BATCH_HEDGE - 0.5):
                hedged = True; futs.add(second())     # hedge: first one still unanswered after 60 s, or failed fast (one immediate retry)
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
    out = {}
    for i, c in ids.items():
        v = (ans or {}).get(i)
        if _valid_one(v):
            res = _verdict(v); jsave(_cfile(c, cache), res); out[c] = res
    return out


def check_rows(rows, cache, skip=(), batch=False):
    """Visual check of every row's clip: cached verdicts first, the rest 4 clips per Flash-low request (up to 4 requests parallel, hard 120 s timeout, hedge after 60 s);
    clips missing/invalid in a batch answer, or a failed batch, fall back to the single-clip call. batch=False = old path (one call per clip, 8 parallel). Rows in `skip` =
    replaced by a card/own graphic anyway. row['flagged'] = a mark/text card was seen, row['crop'] = edge side whose strip removes it."""
    from concurrent.futures import ThreadPoolExecutor
    Path(cache).mkdir(parents=True, exist_ok=True); todo = [r for r in rows if r["clip"] and r["i"] not in skip]
    res = {}
    if batch:
        uniq = list(dict.fromkeys(r["clip"] for r in todo))
        for c in uniq:
            if _cfile(c, cache).exists(): res[c] = jload(_cfile(c, cache))
        pend = [c for c in uniq if c not in res]
        groups = [pend[k:k + BATCH_N] for k in range(0, len(pend), BATCH_N)]
        single = threading.BoundedSemaphore(BATCH_PAR)
        def work(g):
            try: got = _check_batch(g, cache)
            except Exception as e: print("  batch check failed:", str(e)[:80]); got = {}
            for c in g:
                if c not in got:
                    with single: got[c] = clip_check(c, cache)
            return got
        if groups:
            with ThreadPoolExecutor(min(BATCH_PAR, len(groups))) as ex:
                for got in ex.map(work, groups): res.update(got)
    else:
        with ThreadPoolExecutor(8) as ex:
            for r, v in zip(todo, ex.map(lambda r: clip_check(r["clip"], cache), todo)): res[r["clip"]] = v
    for r in todo:
        v = res[r["clip"]]
        r["flagged"] = bool(v["bad"]); r["crop"] = v["side"]; r["marks"] = [m.get("what") for m in v["marks"]]; r["text_card"] = v["text_card"]
    print(f"  visual check: {sum(r['flagged'] for r in rows)} flagged ({sum(1 for r in rows if r['flagged'] and r['crop'])} croppable) of {len(todo)} checked clips")
