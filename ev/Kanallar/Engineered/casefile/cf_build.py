"""Step 3: timeline from the plan, one ffmpeg segment per item (cached), concat, audio, mux. Locked to the voice: each item = its EDL window."""
import random, re, subprocess, io, functools
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import cf_gfx as G
from cf_common import *
from cf_common import _ff

CODE = "v6"
LT_POS = {"FULL": (70, 790), "PRINT": (90, 880), "COLLAGE": (90, 880), "MONITOR": (300, 820)}
OVR = {"3D": "MONITOR", "PHOTO": "PRINT", "ANIM": "FULL"}


@functools.lru_cache(None)
def bars(clip):
    """Baked-in pillar/letterbox bars of a source clip (uniform near-white or near-black edge strips): (x, y, w, h) of the real picture."""
    ims = []
    for ss in ("0.4", "1.6"):
        with _ff:
            p = subprocess.run(["ffmpeg", "-v", "error", "-ss", ss, "-i", clip, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if p.stdout: ims.append(np.asarray(Image.open(io.BytesIO(p.stdout)).convert("L"), np.float32))
    if not ims: return None
    a = np.stack(ims); H, W = a.shape[1:]
    def edge(prof_mean, prof_std, n):
        ok = ((prof_std < 6) & ((prof_mean > 185) | (prof_mean < 14))).tolist(); k = 0
        while k < n // 2 and ok[k]: k += 1
        return k
    cm, cs = a.mean((0, 1)), a.std(1).max(0); rm, rs = a.mean((0, 2)), a.std(2).max(0)
    l, r = edge(cm, cs, W), edge(cm[::-1], cs[::-1], W); t, b = edge(rm, rs, H), edge(rm[::-1], rs[::-1], H)
    if l < W * .03 or r < W * .03: l = r = 0
    if t < H * .03 or b < H * .03: t = b = 0
    return (l, t, W - l - r, H - t - b) if (l or t) else None


CROPS = {"top": "crop=iw:ih*0.88:0:ih*0.12", "bottom": "crop=iw:ih*0.88:0:0", "left": "crop=iw*0.88:ih:iw*0.12:0", "right": "crop=iw*0.88:ih:0:0"}


def fit(clip, flag, src, dst, w, h, base, extra=""):
    """filters: clip stream `src` -> `dst` filling w x h. Baked bars cropped; `flag` = edge side ('top'/'bottom'/'left'/'right') whose <=12% strip holds a mark and is cut off;
    non-16:9 picture (vertical phone clips) gets a blurred darkened copy of itself behind instead of bars."""
    bx = bars(clip); f = [base]
    if bx: f.append(f"crop={bx[2]}:{bx[3]}:{bx[0]}:{bx[1]}")
    if flag in CROPS: f.append(CROPS[flag])
    ar = (bx[2] / bx[3]) if bx else 16 / 9
    pre = ",".join(f)
    if ar < (w / h) * .75:
        return [f"{src}{pre},split[a{dst}][b{dst}]", f"[a{dst}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=24:3,eq=brightness=-.3:saturation=.7[k{dst}]",
                f"[b{dst}]scale={w}:{h}:force_original_aspect_ratio=decrease[g{dst}]", f"[k{dst}][g{dst}]overlay=(W-w)/2:(H-h)/2{extra}[{dst}]"]
    return [f"{src}{pre},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}{extra}[{dst}]"]


def nfr(a, b):
    return round(b * FPS) - round(a * FPS)


def own_card(narr, sents, a, b):
    """Number card if the narration holds exactly one plain number (not a year) followed by a label; else a quote card of the FULL sentence(s)
    overlapping the row window (never a mid-sentence fragment). No invented facts."""
    t = " ".join(narr.split()) or "..."
    nums = re.findall(r"\d[\d,]*(?:\.\d+)?", t)
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s+([A-Za-z][A-Za-z-]*(?:\s+[A-Za-z-]+){0,2})", t)
    if len(nums) == 1 and m and not re.fullmatch(r"(19|20)\d\d", m[1]):
        lab = re.split(r"\b(?:and|that|which|of|to|in|on|at|but|was|were|is|are|with|for)\b", m[2])[0].strip()
        if lab: return "number", dict(kicker="", value=m[1], label=lab)
    ov = [x for x in sents if min(x[1], b) - max(x[0], a) > .5]
    full = " ".join(x[2] for x in ov)
    if not ov or len(full.split()) > 38:
        mid = (a + b) / 2; ov = [x for x in sents if x[0] <= mid <= x[1]] or ov[:1]; full = " ".join(x[2] for x in ov)
    return "quote", dict(text=" ".join(full.split()) or t, by="From the narration")


def timeline(F, plan, flow_dir):
    rows = F["rows"]; secs = plan["sections"]; items = []
    cardrow = {c["rows"][0]: c for c in plan["cards"]}; incard = {r for c in plan["cards"] for r in range(c["rows"][0], c["rows"][1] + 1)}
    lts = {}
    for l in plan["lower_thirds"]:
        lts.setdefault(l["row"], []).append(l)
    skip = set(); lastq = [-99.0]
    bad = lambda r: bool(r["clip"]) and r["flagged"] and not r["crop"] and not (flow_dir / f"row{r['i']:04d}.mp4").exists()   # needs replacing
    real = lambda r: bool(r["clip"]) and r["cat"] not in ("MOTION", "CARD") and (not r["flagged"] or bool(r["crop"]))   # clean or croppable footage
    shown = {r["i"] for r in rows if real(r) and r["i"] not in incard}
    spare = [r["i"] for r in rows if real(r) and r["i"] not in shown]; dups = [r["i"] for r in rows if r["i"] in shown]

    def take_spare(i):
        """Nearest clean clip not shown elsewhere (clips of rows covered by cards); else a clean clip shown >40 s away. Each used once."""
        for pool, gap in ((spare, 0), (dups, 40)):
            ok = [x for x in pool if abs(rows[x - 1]["start"] - rows[i - 1]["start"]) >= gap]
            if ok:
                x = min(ok, key=lambda q: abs(q - i)); pool.remove(x); return x
        return None
    for k, s in enumerate(secs):
        end = (secs[k + 1]["first_row"] - 1) if k + 1 < len(secs) else len(rows)
        i, last = s["first_row"], end
        sec_items = []
        if k > 0 and s["title"] and i not in incard:     # section card eats the first >= 3 s of the part
            j = i
            while j < last and rows[j - 1]["end"] - rows[i - 1]["start"] < 3.0 and (j + 1) not in incard:
                j += 1
            sec_items.append(dict(type="card", kind="section", spec=dict(kicker=s["kicker"], title=s["title"], tease=s["tease"]), a=rows[i - 1]["start"], b=rows[j - 1]["end"]))
            i = j + 1
        while i <= last:
            r = rows[i - 1]
            if i in cardrow:
                c = cardrow[i]; j = c["rows"][1]
                sec_items.append(dict(type="card", kind=c["kind"], spec={x: v for x, v in c.items() if x not in ("rows", "kind")}, a=r["start"], b=rows[j - 1]["end"])); i = j + 1; continue
            fl = flow_dir / f"row{i:04d}.mp4"
            clip = str(fl) if fl.exists() else r["clip"]
            lt = [(l["kicker"], l["line"], l["offset"]) for l in lts.get(i, [])]
            weak = r["cat"] in ("MOTION", "CARD") and not fl.exists()          # pipeline card/motion clip -> our own card
            if not weak and clip and not fl.exists() and bad(r):                # visual check saw a mark that a <=12% edge crop cannot remove
                alt = take_spare(i)
                if alt:
                    sec_items.append(dict(type="clip", mode=OVR.get(rows[alt - 1]["cat"], s["mode"]), clip=rows[alt - 1]["clip"], row=i, flag=rows[alt - 1]["crop"], a=r["start"], b=r["end"], sec=k, grade="", lts=lt))
                    i += 1; continue
                weak = True
            if weak:     # own card from this row's narration only
                kind, spec = own_card(r["narr"], F["sents"], r["start"], r["end"])
                prev = (sec_items or items or [{}])[-1]
                if kind == "quote" and (prev.get("own") or r["start"] - lastq[0] < 30):   # too many own quotes: reuse a clean spare clip instead
                    alt = take_spare(i)
                    if alt:
                        sec_items.append(dict(type="clip", mode=OVR.get(rows[alt - 1]["cat"], s["mode"]), clip=rows[alt - 1]["clip"], row=i, flag=rows[alt - 1]["crop"], a=r["start"], b=r["end"], sec=k, grade="", lts=lt))
                    elif prev.get("type") == "clip":
                        prev["b"] = r["end"]
                    else:
                        sec_items.append(dict(type="card", kind=kind, spec=spec, a=r["start"], b=r["end"], own=True)); lastq[0] = r["start"]
                else:
                    sec_items.append(dict(type="card", kind=kind, spec=spec, a=r["start"], b=r["end"], own=kind == "quote"))
                    if kind == "quote": lastq[0] = r["start"]
            elif not clip:
                sec_items.append(dict(type="card", kind="quote", spec=dict(text=r["narr"] or "...", by="From the narration"), a=r["start"], b=r["end"]))
            else:
                mode = OVR.get(r["cat"], s["mode"])
                sec_items.append(dict(type="clip", mode=mode, clip=clip, row=i, flag=r["crop"] if clip == r["clip"] else None, a=r["start"], b=r["end"], sec=k,
                                      grade="warm" if k == len(secs) - 1 and len(secs) > 2 else "cold" if k == 0 else "", lts=lt))
            i += 1
        if sec_items:
            sec_items[0]["dip_in"] = True; sec_items[-1]["dip_out"] = True
        for it in sec_items: it["sec"] = k
        items += sec_items
    end = items[-1]["b"]
    if plan.get("memorial"):
        items.append(dict(type="card", kind="memorial", spec=dict(text=plan["memorial"]["text"]), a=end, b=end + 5.0, sec=len(secs), dip_in=True)); end += 5.0
    items.append(dict(type="card", kind="endcard", spec={}, a=end, b=end + 6.0, sec=len(secs), dip_in=True, dip_out=True))
    return items


def events(items):
    ev = []
    for it in items:
        t = it["a"]
        if it["type"] == "card":
            _, e = G.CARDS[it["kind"]](it["spec"], it["b"] - it["a"], t)
            ev += [(t + x, k, d) for x, k, d in e]
        elif it["mode"] in ("PRINT", "COLLAGE"):
            ev.append((t, "paper_soft", .8))
        elif it["mode"] == "MONITOR":
            ev.append((t, "glitch", .35))
    return ev


def common_tail(cur, it, d, ins, fl, chrome):
    """lower-thirds, chrome/watermark, dips, grain -> [v]"""
    S = G.S
    for kk, (kick, line, off) in enumerate(it.get("lts", [])):
        a = off; b = min(d - .2, off + 3.4)
        if b - a < 1.2: continue
        x, y = LT_POS[it["mode"]]; n = ins.count("-i")
        ins += ["-loop", "1", "-framerate", "25", "-t", f"{d:.3f}", "-i", G.lt_png(kick, line, it["mode"] in ("PRINT", "COLLAGE"))]
        fl.append(f"[{n}:v]format=rgba,fade=t=in:st={a:.2f}:d=0.35:alpha=1,fade=t=out:st={b-.3:.2f}:d=0.3:alpha=1[lt{kk}]")
        fl.append(f"{cur}[lt{kk}]overlay=x='{G.px(x)}-{G.px(60)}*pow(max(0,1-(t-{a:.2f})/.45),2)':y={G.px(y)}:enable='between(t,{a:.2f},{b:.2f})'[l{kk}]")
        cur = f"[l{kk}]"
    if chrome:
        n = ins.count("-i"); ins += ["-loop", "1", "-framerate", "25", "-t", f"{d:.3f}", "-i", chrome]
        fl.append(f"{cur}[{n}:v]overlay=0:0[ch]"); cur = "[ch]"
    post = []
    if it.get("dip_in"): post.append("fade=t=in:st=0:d=0.16:color=black")
    if it.get("dip_out"): post.append(f"fade=t=out:st={d-0.16:.3f}:d=0.16:color=black")
    post += ["noise=alls=4:allf=t", "format=yuv420p"]
    fl.append(f"{cur}{','.join(post)}[v]")


def render(it, F, plan, out, crf):
    S, W, H = G.S, G.px(1920), G.px(1080)
    d = it["b"] - it["a"]; n = nfr(it["a"], it["b"]); px = G.px
    enc = ["-map", "[v]", "-frames:v", str(n), "-r", "25", "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p", "-an", str(out)]
    chrome = None if it.get("kind") == "endcard" else G.chrome_png(F["title"] if len(F["title"]) < 36 else F["film"])
    it.setdefault("mode", "FULL"); it.setdefault("lts", [])
    if it["type"] == "card":
        gen, _ = G.card_frames(it["kind"], it["spec"], n / FPS, it["a"])
        fl = []; ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "25", "-i", "-"]
        common_tail("[0:v]", it, n / FPS, ins, fl, chrome)
        return ffmpeg([*ins, "-filter_complex", ";".join(fl), *enc], stdin_gen=gen)
    # ---- footage segment
    rx, ry = px(680), px(420); s0 = it["a"]
    tri = lambda a, r: f"{r}-abs(mod({a},{2*r})-{r})"
    clip_in = ["-i", it["clip"]]
    m = it["mode"]; fl = []; ang = random.Random(h(it["row"], "rot")).uniform(-3, 3); jx, jy = [random.Random(h(it["row"], q)).randint(-110, 110) for q in "xy"]
    base = f"fps=25,tpad=stop_mode=clone:stop_duration=3,setsar=1"
    if m == "FULL":
        grade = {"warm": ",colorbalance=rs=.06:bs=-.05", "cold": ",colorbalance=bs=.04:rs=-.03"}.get(it.get("grade"), "")
        bar = px(104)
        ins = [*clip_in]
        fl += fit(it["clip"], it.get("flag"), "[0:v]", "fv", int(W * 1.1), int(H * 1.1), base)
        fl.append(f"[fv]crop={W}:{H}:x='(iw-{W})*t/{d:.2f}':y='(ih-{H})/2',eq=saturation=.92:contrast=1.04{grade},"
                  f"drawbox=0:0:{W}:{bar}:black:fill,drawbox=0:{H-bar}:{W}:{bar}:black:fill[bgv]")
        cur = "[bgv]"
    else:
        ins = ["-loop", "1", "-framerate", "25", "-i", G.topo_path() if m == "PRINT" else G.newspaper_png(), *clip_in]
        if m == "MONITOR":
            bgp, bez = G.monitor_assets(); ins = ["-loop", "1", "-framerate", "25", "-i", bgp, *clip_in, "-loop", "1", "-framerate", "25", "-i", bez]
            fl.append(f"[0:v]null[bg]")
        elif m == "PRINT":
            fl.append(f"[0:v]scale={px(2600)}:{px(1500)},crop={W}:{H}:x='{tri(f'{G.DRIFT*S:.3f}*({s0:.2f}+t)', rx)}':y='{tri(f'{G.DRIFT*.45*S:.3f}*({s0:.2f}+t)+{px(60)}', ry)}'[bg]")
        else:
            fl.append(f"[0:v]crop={W}:{H}:x='{tri(f'{1.2*S:.3f}*({s0:.2f}+t)', px(300))}':y='{tri(f'{.7*S:.3f}*({s0:.2f}+t)', px(60))}'[bg]")
        slide = f"{px(130)}*pow(max(0,1-t/0.5),3)"
        if m == "PRINT":
            pw, ph = 1050, 640; cw, chh = px(pw), px(ph)
            plate = G.asset(f"plate_{pw}_{ph}_{it['row']}", lambda: _plate(pw, ph, it["row"]))
            ins += ["-loop", "1", "-framerate", "25", "-i", plate]
            fl += fit(it["clip"], it.get("flag"), "[1:v]", "c", cw, chh, base)
            fl.append(f"[2:v][c]overlay={px(16)}:{px(16)}:shortest=0,format=rgba,rotate={ang:.3f}*PI/180:c=none:ow=rotw({ang:.3f}*PI/180):oh=roth({ang:.3f}*PI/180)[r]")
            cx, cy = 960 + jx, 480 + jy // 3
        elif m == "COLLAGE":
            pw, ph = 1000, 620; cw, chh = px(pw), px(ph)
            ins += ["-loop", "1", "-framerate", "25", "-i", G.tear_mask(cw, chh)]
            fl += fit(it["clip"], it.get("flag"), "[1:v]", "c0", cw, chh, base, ",format=rgba")
            fl.append(f"[2:v]format=gray[mk];[c0][mk]alphamerge,rotate={ang:.3f}*PI/180:c=none:ow=rotw({ang:.3f}*PI/180):oh=roth({ang:.3f}*PI/180)[r]")
            cx, cy = 960 + jx, 470 + jy // 3
        if m in ("PRINT", "COLLAGE"):
            fl.append("[r]split[r1][r2];[r2]colorchannelmixer=rr=0:gg=0:bb=0:aa=.6,boxblur=" + f"{px(14)}:2[sh]")
            fl.append(f"[bg][sh]overlay=x='{px(cx)}-w/2+{px(14)}':y='{px(cy)}-h/2+{px(26)}+{slide}':eof_action=repeat[b2]")
            fl.append(f"[b2][r1]overlay=x='{px(cx)}-w/2':y='{px(cy)}-h/2+{slide}':eof_action=repeat[b3]")
            cur = "[b3]"
            if m == "COLLAGE":
                tp = G.tape_png(pw - 60, ph - 60, cx, cy, ang)
                ins += ["-loop", "1", "-framerate", "25", "-i", tp]
                idx = sum(1 for x in ins if x == "-i") - 1
                fl.append(f"[b3][{idx}:v]overlay=0:0:enable='gte(t,.5)'[b4]"); cur = "[b4]"
        else:   # MONITOR
            iw, ih = px(972), px(572)
            fl += fit(it["clip"], it.get("flag"), "[1:v]", "c", iw, ih, base, ",eq=saturation=.9,fade=t=in:st=0:d=0.3")
            fl.append(f"[bg][c]overlay={px(474)}:{px(164)}[b2];[b2][2:v]overlay=0:0[b3]")
            cur = "[b3]"
    labels = [(k, l, o) for (k, l, o) in it["lts"]]
    it2 = dict(it, lts=labels)
    common_tail(cur, it2, d, ins, fl, chrome)
    return ffmpeg([*ins, "-filter_complex", ";".join(fl), *enc])


def _plate(pw, ph, row):
    from PIL import ImageDraw
    im = G.paper_img(G.px(pw), G.px(ph), seed=row + 3, pad=0, shadow=False); d = ImageDraw.Draw(im)
    G.put(d, 20, ph - 38, f"EXHIBIT · {row:03d}", "cour", 20, (58, 51, 44))
    return im


def run_items(items, F, plan, segdir, S, crf, workers=2):
    segdir.mkdir(parents=True, exist_ok=True); outs = []
    def one(ix_it):
        ix, it = ix_it
        f = segdir / f"{ix:04d}_{it['type']}_{h(it, S, CODE, Path(it.get('clip') or '.').stat().st_mtime if it.get('clip') else 0)}.mp4"
        if not f.exists():
            tmp = f.with_suffix(".part.mp4")
            render(it, F, plan, tmp, crf); tmp.replace(f)
            print(f"  seg {ix}/{len(items)} {it['type']}:{it.get('kind') or it['mode']} {it['a']:.1f}-{it['b']:.1f}", flush=True)
        return f
    with ThreadPoolExecutor(workers) as ex:
        outs = list(ex.map(one, enumerate(items)))
    for stale in segdir.glob("*.mp4"):
        pass
    return outs


def concat(segs, out):
    lst = out.with_suffix(".txt"); lst.write_text("".join(f"file '{Path(s).as_posix()}'\n" for s in segs), encoding="utf8")
    ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
