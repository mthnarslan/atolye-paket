"""HyperFrames text QA: finds text cut off by the frame edge and text sitting on other text, before render.
python hf_metin_qa.py <project dir or index.html> [--step 0.25] [--pad 6] [--json out.json]
Exit 0 = clean, 1 = problems (listed as: TYPE  t_from-t_to  element  detail).
How: headless Chromium opens index.html, seeks window.__timelines.main every --step s, shows only clips whose
data-start/data-duration cover t, and measures every visible element that has its own text (getBoundingClientRect,
so GSAP transforms count; boxes trimmed 18% top/bottom to glyph height; text inside the same
absolutely positioned component, e.g. a meter's label/value/unit, is not compared). Text under an active full-frame video clip is skipped (covered).
CUT     = text box crosses the frame edge (partly visible), e.g. a card whose transform got overwritten by GSAP.
OVERLAP = two visible (effective opacity >= .5) text boxes intersect > 12% of the smaller one."""
import argparse, json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

JS = r"""
([t, pad]) => {
  const W = 1920, H = 1080;
  const clips = [...document.querySelectorAll('[data-start][data-duration]')].filter(e => e.id !== 'root' && !e.matches('[data-composition-id]'));
  let covered = false;
  for (const c of clips) {
    const s = +c.dataset.start, d = +c.dataset.duration, on = t >= s && t < s + d;
    c.style.visibility = on ? 'visible' : 'hidden';
    if (on && c.tagName === 'VIDEO') covered = true;
  }
  window.__timelines.main.seek(t, false);
  if (covered) return {covered: true, items: []};
  const op = el => { let o = 1; for (let e = el; e && e !== document.body; e = e.parentElement) {
      const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; } return o; };
  const items = [];
  for (const el of document.querySelectorAll('#root *')) {
    if (['SCRIPT', 'STYLE', 'svg', 'VIDEO', 'IMG'].includes(el.tagName)) continue;
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    if (!own) continue;
    const o = op(el); if (o < 0.08) continue;
    const r = document.createRange(); r.selectNodeContents(el); const b0 = r.getBoundingClientRect();
    if (b0.width < 2 || b0.height < 2) continue;
    const sh = b0.height * 0.18;   // line box -> approx. glyph box (line-height padding is not a collision)
    const b = {left: b0.left, right: b0.right, top: b0.top + sh, bottom: b0.bottom - sh};
    let comp = el.parentElement;   // nearest absolutely positioned ancestor = one designed component (meter, card...)
    while (comp && comp !== document.body && getComputedStyle(comp).position !== 'absolute') comp = comp.parentElement;
    const name = (el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + [...el.classList].join('.')) + ' "' + own.slice(0, 28) + '"';
    items.push({name, o, x0: b.left, y0: b.top, x1: b.right, y1: b.bottom, el, comp});
  }
  const out = [];
  for (const a of items) {
    const inside = a.x1 > 0 && a.y1 > 0 && a.x0 < W && a.y0 < H;
    const cut = inside && (a.x0 < -pad || a.y0 < -pad || a.x1 > W + pad || a.y1 > H + pad);
    if (cut) out.push(['CUT', a.name, `box ${a.x0|0},${a.y0|0} → ${a.x1|0},${a.y1|0}`]);
  }
  const vis = items.filter(a => a.o >= 0.5);
  for (let i = 0; i < vis.length; i++) for (let j = i + 1; j < vis.length; j++) {
    const a = vis[i], b = vis[j];
    if (a.el.contains(b.el) || b.el.contains(a.el) || (a.comp && a.comp === b.comp)) continue;
    const ix = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0), iy = Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0);
    if (ix <= 0 || iy <= 0) continue;
    const sm = Math.min((a.x1 - a.x0) * (a.y1 - a.y0), (b.x1 - b.x0) * (b.y1 - b.y0));
    if (ix * iy > 0.12 * sm) out.push(['OVERLAP', a.name + ' × ' + b.name, `${(100 * ix * iy / sm) | 0}% of smaller`]);
  }
  return {covered: false, items: out};
}
"""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--step", type=float, default=0.25)
    ap.add_argument("--pad", type=float, default=6); ap.add_argument("--json"); a = ap.parse_args()
    p = Path(a.path); p = p / "index.html" if p.is_dir() else p
    hits = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(viewport={"width": 1920, "height": 1080})
        pg.route("**/*.{mp4,webm,mov,mp3,wav}", lambda r: r.abort())   # media not needed for layout
        pg.goto(p.resolve().as_uri(), wait_until="domcontentloaded")
        pg.wait_for_function("!!(window.__timelines && window.__timelines.main)", timeout=60000, polling=250)
        pg.evaluate("document.fonts.ready.then(() => 1)")
        total = pg.evaluate("window.__timelines.main.duration()")
        t = 0.0
        while t < total:
            r = pg.evaluate(JS, [round(t, 3), a.pad])
            for typ, name, det in r["items"]:
                k = (typ, name); h = hits.setdefault(k, {"t0": t, "t1": t, "det": det, "n": 0}); h["t1"] = t; h["n"] += 1
            t += a.step
        br.close()
    # drop one-sample blips that are mid-animation (a moving element crossing another for < 2 steps)
    rows = sorted(((v["t0"], k[0], k[1], v) for k, v in hits.items() if v["n"] >= 2), key=lambda r: r[0])
    for t0, typ, name, v in rows:
        print(f"{typ:8s} {t0:7.2f}-{v['t1']:7.2f}s  {name}  ({v['det']})")
    print(f"metin_qa: {len(rows)} problem(s), {total:.1f}s checked every {a.step}s")
    if a.json: json.dump([dict(type=k, name=n, **v) for _, k, n, v in rows], open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    sys.exit(1 if rows else 0)

if __name__ == "__main__":
    main()
