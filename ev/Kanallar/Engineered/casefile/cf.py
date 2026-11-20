"""WRATH OF EARTH 'Case File' builder.  python casefile/cf.py <FILM> [--plan|--assets|--build|--preview|--only a-b] [--flow-max N] [--scale S]
Steps are cached under casefile/work/<FILM>/ (plan, flow clips, segments)."""
import argparse, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf8", errors="replace")
import cf_gfx as G, cf_build as B, cf_audio as A, cf_plan as P
from cf_common import *


def flow_step(F, plan, W, flow_max):
    """Style-locked Flow replacements (hook + flagged clips): still -> Omni Flash clip -> crop 6% -> work/flow/rowNNNN.mp4. Max 3 parallel."""
    from concurrent.futures import ThreadPoolExecutor
    import base64
    sys.path.insert(0, r"C:\Users\meteh\SkullStudio\pipeline")
    from common import glabs, flash
    fd = W / "flow"; fd.mkdir(exist_ok=True)
    marked = {r["i"] for r in F["rows"] if r["flagged"]}      # rows with a visible mark first, then the hook
    todo = sorted([f for f in plan["flow"] if not (fd / f"row{f['row']:04d}.mp4").exists()], key=lambda f: f["row"] not in marked)[:flow_max]
    print(f"  flow: {len(plan['flow'])} planned, {len(todo)} to generate now (cap {flow_max})")

    def make(f):
        r = F["rows"][f["row"] - 1]; d = r["end"] - r["start"]; raw = fd / f"row{f['row']:04d}_raw.mp4"; still = fd / f"row{f['row']:04d}.png"
        if not raw.exists():
            if not still.exists():
                note = ""
                for _ in range(2):
                    png = glabs("/api/image/generate", {"prompt": f"{f['action']} {P.STYLE}{note}", "model": "nano_banana_pro", "aspect_ratio": "16:9"}, 600)
                    v = flash("Quality gate for a still. It must show: %r as a vintage engraving on cream paper. Visible text, letters, numbers, logos or "
                              'human faces fail. JSON only: {"pass": true|false, "fix": "one sentence"}' % f["action"], png)
                    still.write_bytes(png)
                    if v.get("pass"): break
                    note = " Fix: " + str(v.get("fix") or "")
            ref = "data:image/png;base64," + base64.b64encode(still.read_bytes()).decode()
            raw.write_bytes(glabs("/api/video/generate", {"prompt": f"ACTION: {f['action']} {P.STYLE} Smooth motion, no cuts.", "model": "omni_flash", "mode": "start_image",
                                                          "aspect_ratio": "16:9", "video_length": 4 if d <= 4 else 6 if d <= 6 else 8, "resolution": ["1080p"], "remove_logo": True,
                                                          "reference_images": [ref]}, 1500))
        stretch = max(1.0, min(1.6, d / (4 if d <= 4 else 6 if d <= 6 else 8)))
        ffmpeg(["-i", str(raw), "-an", "-vf", f"crop=iw*0.88:ih*0.88,scale=1920:1080:flags=lanczos,fps=25,setpts={stretch}*PTS", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(fd / f"row{f['row']:04d}.mp4")])
        return f["row"]
    with ThreadPoolExecutor(3) as ex:
        for r in ex.map(make, todo): print("  flow clip row", r)


def pick_window(items, lo=60, hi=90):
    """Preview window: the item-aligned 60-90 s stretch with the most variety (hook, section card, PRINT, MONITOR, document, number...)."""
    best = (-1, 0, 0)
    for i, it in enumerate(items):
        j = i
        while j + 1 < len(items) and items[j + 1]["b"] - it["a"] <= hi: j += 1
        if items[j]["b"] - it["a"] < lo: continue
        feat = {(x.get("kind") if x["type"] == "card" else x.get("mode")) for x in items[i:j + 1]} | ({"HOOK"} if it["sec"] == 0 else set())
        feat |= {"LT"} if any(x.get("lts") for x in items[i:j + 1]) else set()
        sc = len(feat) + (1.5 if "section" in feat else 0) + (1 if "document" in feat else 0) + (1 if "number" in feat else 0) + (1 if "MONITOR" in feat else 0)
        if sc > best[0]: best = (sc, i, j)
    return best[1], best[2]


def contact_sheets(final, q, dur, every=10, cols=4, rows=3, items=()):
    """One frame per `every` s, each grabbed with its own fast seek (the fps/tile filter chain dropped all but 2), tiled 4x3."""
    from PIL import Image, ImageDraw
    for old in q.glob("contact_*.jpg"): old.unlink()
    ts = [t + 0.5 for t in range(0, int(dur), every)]; per = cols * rows
    t_off = items[0]["a"] if items else 0
    for k, t in enumerate(ts):    # a sample inside a graphic card moves to its finished state (typewriter/pen done), not mid-animation
        for it in items:
            if it["type"] == "card" and it["a"] - t_off <= t < it["b"] - t_off and it["b"] - it["a"] >= 3: ts[k] = max(t, it["b"] - t_off - 0.8); break
    for n in range(0, len(ts), per):
        sheet = Image.new("RGB", (480 * cols, 270 * rows))
        for k, t in enumerate(ts[n:n + per]):
            f = q / "_f.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(final), "-frames:v", "1", "-vf", "scale=480:270", str(f)])
            if f.exists():
                im = Image.open(f).convert("RGB"); ImageDraw.Draw(im).text((6, 4), f"{t:.0f}s", fill=(255, 255, 0))
                sheet.paste(im, (480 * (k % cols), 270 * (k // cols))); f.unlink()
        sheet.save(q / f"contact_{n // per + 1:02d}.jpg", quality=85)


def qa(final, W, F, items, t0, t1):
    q = W / "qa"; q.mkdir(exist_ok=True); lines = [f"# CASEFILE_QA {F['film']}", ""]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(final)], capture_output=True, text=True).stdout)
    lines.append(f"- video duration {dur:.2f}s; timeline window {t0:.1f}-{t1:.1f}s ({t1 - t0:.2f}s) -> delta {dur - (t1 - t0):+.2f}s")
    for sec in sorted({it["sec"] for it in items}):
        its = [x for x in items if x["sec"] == sec]; a, b = its[0]["a"] - t0, min(its[-1]["b"] - t0, dur)
        if b - a < 3: continue
        r = subprocess.run(["ffmpeg", "-nostats", "-ss", f"{a:.2f}", "-t", f"{b-a:.2f}", "-i", str(final), "-vn", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
        lines.append(f"- section {sec}: LUFS {m[-1] if m else 'n/a'} ({a:.0f}-{b:.0f}s)")
    contact_sheets(final, q, dur, items=items)
    lines.append("- contact grids every 10 s in qa/contact_*.jpg (check overlap, cropped text, empty frames, leftover watermark by eye)")
    (W / "CASEFILE_QA.md").write_text("\n".join(lines) + "\n", encoding="utf8"); print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("film")
    for f in ("plan", "assets", "build", "preview", "force-plan"): ap.add_argument("--" + f, action="store_true")
    ap.add_argument("--only"); ap.add_argument("--flow-max", type=int, default=10); ap.add_argument("--scale", type=float)
    a = ap.parse_args()
    steps = a.plan or a.assets or a.build or a.preview or a.only
    S = a.scale or (0.5 if (a.preview or a.only) else 1.0); G.setscale(S)
    W = HERE / "work" / a.film; W.mkdir(parents=True, exist_ok=True)
    F = load_film(a.film)
    print(f"{a.film}: {len(F['rows'])} rows, {F['total']:.0f}s, {sum(1 for r in F['rows'] if r['clip'])} clips present, title {F['title']!r}")
    plan = P.make_plan(F, W, force=a.force_plan) if (not steps or a.plan or a.assets or a.build or a.preview or a.only) else None
    if plan is not None:
        weak = {r["i"] for r in F["rows"] if r["cat"] in ("MOTION", "CARD")} | {i for c in plan["cards"] for i in range(c["rows"][0], c["rows"][1] + 1)}
        weak |= {r["i"] for r in F["rows"] if (W / "flow" / f"row{r['i']:04d}.mp4").exists()}
        check_rows(F["rows"], W / "clipcheck", skip=weak)
        P.extend_flow(F, plan, W, weak)
    if a.plan and not (a.assets or a.build or a.preview or a.only): return
    if not steps or a.assets:
        flow_step(F, plan, W, a.flow_max)
        if a.assets: return
    items = B.timeline(F, plan, W / "flow")
    t0, t1 = items[0]["a"], items[-1]["b"]
    if a.preview or a.only:
        if a.only:
            lo, hi = map(float, a.only.split("-")); idx = [i for i, x in enumerate(items) if x["b"] > lo and x["a"] < hi]; i0, i1 = idx[0], idx[-1]
        else:
            i0, i1 = pick_window(items)
        items = items[i0:i1 + 1]; t0, t1 = items[0]["a"], items[-1]["b"]
    tag = "preview" if (a.preview or a.only) else "full"
    print(f"building {tag}: {len(items)} items, {t0:.1f}-{t1:.1f}s, scale {S}; kinds:",
          sorted({(x.get('kind') if x['type'] == 'card' else x['mode']) for x in items}))
    segs = B.run_items(items, F, plan, W / f"seg_{S}", S, 23 if S < 1 else 19)
    vid = W / f"_video_{tag}.mp4"; B.concat(segs, vid)
    vn = A.voice_norm(F["voice"], W / "voice_n16.wav")
    allitems = B.timeline(F, plan, W / "flow")
    wav = W / f"_audio_{tag}.wav"; A.build(items, B.events(allitems), t0, t1, vn, wav, W)
    out = (W / f"CASEFILE_PREVIEW_{int(t0)}-{int(t1)}.mp4") if tag == "preview" else DELIVERY / a.film / f"{a.film}_WRATH_OF_EARTH_CASEFILE.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(["-i", str(vid), "-i", str(wav), "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", str(out)])
    print("wrote", out)
    qa(out, W, F, items, t0, t1)


if __name__ == "__main__":
    main()
