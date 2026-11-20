"""Scene library for the WRATH OF EARTH script-first edit (the logic of the 1-min Enderlin sample, ornek/tools/build_hf.py).
Every scene: fn(sid, s, d, beats, p) -> (html, js, events). s = absolute start, d = duration, beats = scene-relative start of each
sentence in the scene, p = the planner's fields. events = [(abs_time, sfx_kind, dur)] for the mixer."""
import html as H
import re

INK, PAPER, RED = "#0B0F10", "#E8E2D3", "#C02622"
FONTS = """
@font-face{font-family:'WGaramond';src:url('assets/fonts/GARA.TTF')}
@font-face{font-family:'WGaramond';src:url('assets/fonts/GARAIT.TTF');font-style:italic}
@font-face{font-family:'WBodoni';src:url('assets/fonts/BOD_R.TTF')}
@font-face{font-family:'WBahn';src:url('assets/fonts/bahnschrift.ttf')}
@font-face{font-family:'WCourier';src:url('assets/fonts/cour.ttf')}
@font-face{font-family:'WScript';src:url('assets/fonts/segoesc.ttf')}
"""
BASE_CSS = f"""
#root{{position:absolute;inset:0;overflow:hidden;background:{INK};color:{PAPER}}}
.bgwrap{{position:absolute;left:0;top:0;width:2600px;height:1500px}}
.bgwrap img{{width:2600px;height:1500px;display:block}}
.lab{{font-family:'WBahn';letter-spacing:.32em;text-transform:uppercase;font-size:22px;color:rgba(232,226,211,.72)}}
.gar{{font-family:'WGaramond'}}
.bod{{font-family:'WBodoni'}}
.paper{{background:{PAPER};color:#1a1714;box-shadow:0 30px 60px rgba(0,0,0,.55),0 4px 10px rgba(0,0,0,.4)}}
.note{{font-family:'WScript';color:{RED}}}
.tag{{position:absolute;left:0;right:0;bottom:46px;text-align:center;font-family:'WBahn';font-size:18px;letter-spacing:.4em;color:rgba(232,226,211,.5)}}
"""


def e(t):
    return H.escape(str(t or ""))


def r3(x):
    return round(x, 3)


def bg(sid, s, d, img="topo.jpg"):
    """one continuous drift across the whole film (x = -8 px per film second), slow push-in"""
    s0 = s % 160   # keep the image on screen: the drift wraps every 160 s (at a scene cut, never inside a scene)
    return (f'<div id="{sid}-bg" class="bgwrap"><img src="assets/img/{img}" alt=""></div>',
            f'tl.fromTo("#{sid}-bg",{{x:{-4*s0-200:.1f},y:{-1.5*s0-180:.1f},scale:{1+0.001*s0:.4f}}},'
            f'{{x:{-4*(s0+d)-200:.1f},y:{-1.5*(s0+d)-180:.1f},scale:{1+0.001*(s0+d):.4f},duration:{d},ease:"none"}},0);')


def lower_third(i, kicker, line, x, y, t_in, t_out):
    if not (kicker or line):
        return "", ""
    h = (f'<div id="{i}" style="position:absolute;left:{x}px;top:{y}px;padding:18px 40px 20px 26px;max-width:1100px;'
         f'background:linear-gradient(90deg,rgba(11,15,16,.85),rgba(11,15,16,.6) 70%,rgba(11,15,16,0));border-left:3px solid {RED};opacity:0">'
         f'<div class="lab" style="font-size:20px">{e(kicker)}</div>'
         f'<div style="height:1px;background:rgba(232,226,211,.45);margin:10px 0 10px;width:100%"></div>'
         f'<div class="gar" style="font-size:44px;letter-spacing:.04em">{e(line)}</div></div>')
    j = (f'tl.fromTo("#{i}",{{opacity:0,x:-60}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{r3(t_in)});'
         f'tl.to("#{i}",{{opacity:0,duration:.35}},{r3(max(t_in + .8, t_out))});')
    return h, j


def circle_svg(i, chars, size, line, padx=26, pady=12, stroke=5):
    W, Hh = chars * 0.6 * size + 2 * padx, line + 2 * pady
    pts = [(120, 4), (205, 4), (204, 96), (100, 96), (-4, 96), (-6, 2), (128, 8)]
    q = [f"{x*W/200:.1f} {y*Hh/100:.1f}" for x, y in pts]
    d = f"M {q[0]} C {q[1]} {q[2]} {q[3]} C {q[4]} {q[5]} {q[6]}"
    return (f'<svg width="{W:.0f}" height="{Hh:.0f}" viewBox="0 0 {W:.0f} {Hh:.0f}" style="position:absolute;left:-{padx}px;top:-{pady}px;overflow:visible">'
            f'<path id="{i}" d="{d}" fill="none" stroke="{RED}" stroke-width="{stroke}" stroke-linecap="round" '
            f'pathLength="100" stroke-dasharray="100 100" stroke-dashoffset="100" opacity=".92"/></svg>')


def draw(i, t, dur=.6):
    return f'tl.fromTo("#{i}",{{attr:{{"stroke-dashoffset":100}}}},{{attr:{{"stroke-dashoffset":0}},duration:{dur},ease:"power1.inOut"}},{r3(t)});'


def typed(i, t, dur):
    return (f'tl.fromTo("#{i}",{{clipPath:"inset(-40px 100% -40px -40px)"}},{{clipPath:"inset(-40px -80px -40px -40px)",'
            f'duration:{r3(dur)},ease:"steps({max(4,int(dur*22))})"}},{r3(t)});')


def num_parts(txt):
    """'2,250' -> (2250, 'comma', ''), '300+' -> (300, 'int', '+'), '0.5' -> None (shown static)"""
    m = re.fullmatch(r"\s*([\d,]+)\s*(\+?)\s*", str(txt))
    if not m:
        return None
    v = int(m.group(1).replace(",", ""))
    return v, ("comma" if v >= 10000 or "," in m.group(1) else "int"), m.group(2)


def counter(i, t, txt, dur=1.0):
    np_ = num_parts(txt)
    if not np_ or np_[0] < 2 or (np_[0] > 1900 and np_[0] < 2100 and "," not in str(txt)):   # years and tiny numbers: no count-up
        return ""
    v, fmt, suf = np_
    f = "Math.round(o.v).toLocaleString('en-US')" if fmt == "comma" else "Math.round(o.v)"
    return (f'(function(){{const o={{v:0}};const el=document.querySelector("#{i}");'
            f'tl.fromTo(o,{{v:0}},{{v:{v},duration:{dur},ease:"power2.out",onUpdate:()=>{{el.textContent={f}+"{suf}";}}}},{r3(t)});}})();')


def video(i, src, dur, style):
    return f'<video id="{i}" class="clip" src="{src}" muted playsinline data-start="0" data-duration="{r3(dur)}" style="{style}"></video>'


def print_frame(i, src, x, y, w, h, rot, t_in, dur, label):
    html = (f'<div id="{i}" class="paper" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;padding:16px 16px 52px;opacity:0">'
            f'<video id="{i}-v" class="clip" src="{src}" muted playsinline data-start="{r3(t_in)}" data-duration="{r3(dur - t_in)}" '
            f'style="width:100%;height:100%;object-fit:cover;display:block"></video>'
            f'<div style="position:absolute;left:18px;bottom:14px;font-family:WCourier;font-size:18px;color:#3a332c">{e(label)}</div></div>')
    js = f'tl.fromTo("#{i}",{{y:120,rotation:{rot-6},opacity:0}},{{y:0,rotation:{rot},opacity:1,duration:.5,ease:"power3.out"}},{r3(t_in)});'
    return html, js


def beat(beats, k, d, default=.4):
    """scene-relative time of sentence k (clamped), small lead-in"""
    if k is None:
        return default
    k = max(0, min(int(k), len(beats) - 1))
    return min(d - .8, beats[k] + (default if k == 0 else .25))


def fade_out(d, sel="#root", dur=.3):
    return f'tl.to("{sel}",{{opacity:0,duration:{dur}}},{r3(d - dur - .02)});'


# ------------------------------------------------------------------------------------------------ scene types
def sc_full(sid, s, d, b, p, clips):
    """Flow engraving clip or real footage, full frame, letterbox, slow push; a 2nd clip cuts in on a later sentence"""
    ids = clips[:2]
    cut = beat(b, 1, d, 0) if len(ids) > 1 and len(b) > 1 else d
    if len(ids) > 1 and (cut < 2.5 or d - cut < 2.5):
        cut = d / 2 if d >= 6 else d
        if cut == d: ids = ids[:1]
    vids = video(f"{sid}-v0", ids[0], cut, "position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:cover")
    if len(ids) > 1:
        vids += (f'<video id="{sid}-v1" class="clip" src="{ids[1]}" muted playsinline data-start="{r3(cut)}" data-duration="{r3(d-cut)}" '
                 f'style="position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:cover"></video>')
    lh, lj = lower_third(f"{sid}-lt", p.get("kicker"), p.get("line"), 110, 730, .5, d - .6)
    h = (f'<div id="{sid}-w" style="position:absolute;inset:0">{vids}</div>'
         f'<div style="position:absolute;left:0;top:0;width:1920px;height:104px;background:#000"></div>'
         f'<div style="position:absolute;left:0;bottom:0;width:1920px;height:104px;background:#000"></div>' + lh)
    j = f'tl.fromTo("#{sid}-w",{{scale:1.06}},{{scale:1.13,duration:{r3(d)},ease:"none"}},0);' + lj
    ev = [(s, "whoosh", 1.6)] if p.get("whoosh") else []
    return h, j, ev, True


def sc_print(sid, s, d, b, p, clips):
    """1-2 evidence prints sliding onto the map table; the 2nd lands on a later sentence"""
    h, j, ev = "", "", [(s, "paper", .8)]
    p1h, p1j = print_frame(f"{sid}-pa", clips[0], 230, 150, 1150, 700, -2.2, 0, d, p.get("label_a") or "EXHIBIT · A")
    h += p1h; j += p1j
    if len(clips) > 1:
        t2 = beat(b, 1, d, 0) if len(b) > 1 else d / 2
        t2 = min(max(t2, 2.2), d - 2.2)
        p2h, p2j = print_frame(f"{sid}-pb", clips[1], 860, 300, 860, 530, 2.6, t2, d, p.get("label_b") or "EXHIBIT · B")
        h += p2h; j += p2j + f'tl.to("#{sid}-pa",{{x:-120,filter:"brightness(.55)",duration:.5}},{r3(t2)});'
        ev.append((s + t2, "paper", .8))
    lh, lj = lower_third(f"{sid}-lt", p.get("kicker"), p.get("line"), 90, 880, .7, d - .5)
    return h + lh, j + lj + fade_out(d, f"#{sid}-pa,#{sid}-pb" if len(clips) > 1 else f"#{sid}-pa", .3), ev, False


def sc_print_number(sid, s, d, b, p, clips):
    t = beat(b, p.get("at"), d, .9)
    ph, pj = print_frame(f"{sid}-pa", clips[0], 110, 170, 1050, 640, -2.5, 0, d, p.get("label_a") or "EXHIBIT")
    num = e(p.get("number"))
    h = ph + f'''
<div id="{sid}-a" style="position:absolute;left:1240px;top:270px;opacity:0;max-width:600px">
 <div class="bod" style="font-size:{200 if len(num) <= 5 else 140}px;line-height:1"><span id="{sid}-n">{num}</span><span style="font-size:60px"> {e(p.get("unit"))}</span></div>
 <div id="{sid}-u" style="height:4px;width:320px;background:{RED};transform-origin:left center;margin:16px 0 18px"></div>
 <div class="lab" style="font-size:24px;line-height:1.6">{e(p.get("label"))}</div>
 <div class="lab" style="font-size:16px;margin-top:22px;opacity:.75">{e(p.get("source"))}</div></div>'''
    j = (pj + f'tl.fromTo("#{sid}-a",{{opacity:0,x:30}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{r3(t)});' + counter(f"{sid}-n", t, p.get("number"))
         + f'tl.fromTo("#{sid}-u",{{scaleX:0}},{{scaleX:1,duration:.45,ease:"power2.out"}},{r3(t+.6)});' + fade_out(d, f"#{sid}-pa,#{sid}-a"))
    return h, j, [(s, "paper", .8), (s + t, "sub", 2.2), (s + t + .6, "penline", .45)], False


def sc_number(sid, s, d, b, p, clips):
    t = beat(b, p.get("at"), d, .5)
    num = e(p.get("number"))
    sub = p.get("sub")
    h = f'''
<div id="{sid}-k" class="lab" style="position:absolute;left:0;right:0;top:290px;text-align:center;opacity:0">{e(p.get("kicker"))}</div>
<div id="{sid}-yr" style="position:absolute;left:0;right:0;top:340px;text-align:center;opacity:0"><span id="{sid}-n" class="bod" style="font-size:{250 if len(num) <= 5 else 170}px;line-height:1;letter-spacing:.04em">{num}</span><span class="bod" style="font-size:80px"> {e(p.get("unit"))}</span></div>
<div id="{sid}-u" style="position:absolute;left:760px;top:640px;width:400px;height:4px;background:{RED};transform-origin:center"></div>
<div id="{sid}-l" class="gar" style="position:absolute;left:160px;right:160px;top:680px;text-align:center;font-size:52px;letter-spacing:.18em;opacity:0">{e(p.get("label"))}</div>
<div id="{sid}-s" class="lab" style="position:absolute;left:0;right:0;top:800px;text-align:center;font-size:20px;opacity:0">{e(sub)}</div>'''
    j = (f'tl.fromTo("#{sid}-k",{{opacity:0}},{{opacity:1,duration:.6}},{r3(max(.1,t-.3))});'
         f'tl.fromTo("#{sid}-yr",{{opacity:0,scale:1.06}},{{opacity:1,scale:1,duration:.9,ease:"power2.out"}},{r3(t)});' + counter(f"{sid}-n", t, p.get("number"), 1.2)
         + f'tl.fromTo("#{sid}-u",{{scaleX:0}},{{scaleX:1,duration:.5,ease:"power2.out"}},{r3(t+.9)});'
         f'tl.fromTo("#{sid}-l",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.6}},{r3(t+1.0)});'
         f'tl.fromTo("#{sid}-s",{{opacity:0}},{{opacity:1,duration:.5}},{r3(beat(b, 1, d, 0) if len(b) > 1 else t+1.6)});' + fade_out(d, "#root", .35))
    return h, j, [(s + t, "sub", 2.2), (s + t + .9, "penline", .45)], False


def sc_document(sid, s, d, b, p, clips):
    lines = [l for l in (p.get("lines") or []) if isinstance(l, (list, tuple)) and len(l) == 2][:5]
    ring, strike = p.get("ring"), p.get("strike")
    rows = ""
    for k, (key, val) in enumerate(lines):
        v = e(val)
        if k == ring:
            v = f'<span style="position:relative;display:inline-block;font-weight:bold">{v}{circle_svg(f"{sid}-c", len(str(val)), 36, 50)}</span>'
        st = (f'<div id="{sid}-x" style="position:absolute;left:-10px;right:0;top:24px;height:5px;background:{RED};transform-origin:left center"></div>'
              if k == strike else "")
        rows += f'<div id="{sid}-l{k}" style="position:relative;margin-top:{18 if k else 34}px">{e(key)} {"." * max(3, 16 - len(str(key)))} {v}{st}</div>'
    ph = min(830, 380 + 96 * len(lines) + (90 if p.get("note") else 0)); top = (1080 - ph) // 2
    h = f'''
<div id="{sid}-doc" class="paper" style="position:absolute;left:330px;top:{top}px;width:1260px;height:{ph}px;padding:60px 80px;font-family:WCourier;font-size:36px;line-height:1.5">
 <div id="{sid}-h0" style="font-size:24px;letter-spacing:.12em">{e(p.get("header"))}</div>
 <div style="height:2px;background:#1a1714;margin:14px 0 26px"></div>
 <div id="{sid}-h1" style="font-size:42px;font-weight:bold;line-height:1.3">{e(p.get("title"))}</div>
 {rows}
 <div id="{sid}-note" class="note" style="position:absolute;right:90px;bottom:70px;font-size:42px;transform:rotate(-5deg);opacity:0">{e(p.get("note"))}</div>
 <div style="position:absolute;left:70px;bottom:36px;font-family:WBahn;font-size:16px;letter-spacing:.35em;color:#6b6258">ILLUSTRATIVE LAYOUT</div>
</div>'''
    j = f'tl.fromTo("#{sid}-doc",{{y:420,rotation:-7,opacity:0}},{{y:0,rotation:-1.4,opacity:1,duration:.55,ease:"power3.out"}},0);'
    ev = [(s, "paper", .8)]
    t = .45; avail = max(2.0, d - 2.6); per = avail / (2 + len(lines))
    j += typed(f"{sid}-h0", t, min(.6, per)); t += min(.6, per)
    j += typed(f"{sid}-h1", t, min(1.1, per)); ev.append((s + .45, "type", min(.6, per) + min(1.1, per))); t += min(1.1, per) + .1
    for k in range(len(lines)):
        j += typed(f"{sid}-l{k}", t, min(.8, per)); ev.append((s + t, "type", min(.8, per))); t += min(.8, per) + .08
        if k == ring:
            j += draw(f"{sid}-c", t, .7); ev.append((s + t, "pen", .75)); t += .75
        if k == strike:
            j += f'tl.fromTo("#{sid}-x",{{scaleX:0}},{{scaleX:1,duration:.45,ease:"power1.inOut"}},{r3(t)});'; ev.append((s + t, "penline", .45)); t += .5
    if p.get("note"):
        j += f'tl.fromTo("#{sid}-note",{{opacity:0}},{{opacity:1,duration:.4}},{r3(min(t, d - 1.0))});'
    j += f'tl.to("#{sid}-doc",{{y:-60,opacity:0,duration:.35,ease:"power2.in"}},{r3(d-.37)});'
    return h, j, ev, False


def sc_monitor(sid, s, d, b, p, clips):
    grid = "".join(f'<line x1="{960+(i-12)*40}" y1="560" x2="{960+(i-12)*260}" y2="1080" stroke="rgba(192,38,34,.28)" stroke-width="1.5"/>' for i in range(25))
    grid += "".join(f'<line x1="0" y1="{560+k*k*7}" x2="1920" y2="{560+k*k*7}" stroke="rgba(192,38,34,.22)" stroke-width="1.5"/>' for k in range(1, 10))
    lh, lj = lower_third(f"{sid}-lt", p.get("kicker"), p.get("line"), 300, 820, .6, d - .5)
    h = (f'<svg width="1920" height="1080" style="position:absolute;left:0;top:0">{grid}</svg>'
         f'<div id="{sid}-mon" style="position:absolute;left:460px;top:150px;width:1000px;height:600px;background:#050607;border:14px solid #15191a;border-radius:10px;'
         f'box-shadow:0 0 50px rgba(160,200,210,.18),0 0 0 2px rgba(200,220,225,.25);overflow:hidden">'
         + video(f"{sid}-v", clips[0], d, "width:100%;height:100%;object-fit:cover") + '</div>'
         '<div style="position:absolute;left:930px;top:764px;width:60px;height:120px;background:#121516"></div>'
         '<div style="position:absolute;left:840px;top:880px;width:240px;height:14px;background:#121516;border-radius:4px"></div>' + lh)
    j = (f'tl.fromTo("#{sid}-mon",{{scale:.94,opacity:0}},{{scale:1,opacity:1,duration:.5,ease:"power2.out"}},0);'
         f'tl.fromTo("#{sid}-mon",{{x:-14}},{{x:14,duration:{r3(d)},ease:"none"}},0);' + lj)
    return h, j, [(s, "glitch", .4)], True


def sc_map(sid, s, d, b, p, clips):
    stops = [x for x in (p.get("stops") or []) if x][:5]
    n = max(2, len(stops))
    pts = [(260 + k * (1400 / (n - 1)), 760 - k * (420 / (n - 1)) + (60 if k % 2 else 0)) for k in range(n)]
    path = "M " + " L ".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    t0 = .9; span = max(1.5, min(d - 2.5, (beats_span := (b[-1] if len(b) > 1 else d * .5)) + 1.2))
    labs = "".join(
        f'<div id="{sid}-s{k}" style="position:absolute;left:{x-9:.0f}px;top:{y-9:.0f}px;opacity:0"><div style="width:18px;height:18px;border-radius:50%;background:{RED};box-shadow:0 0 0 6px rgba(192,38,34,.25)"></div>'
        f'<div class="gar" style="position:absolute;left:30px;top:{-58 if k % 2 == 0 else 22}px;white-space:nowrap;font-size:38px">{e(st)}</div></div>'
        for k, ((x, y), st) in enumerate(zip(pts, stops)))
    h = f'''
<div class="lab" id="{sid}-k" style="position:absolute;left:150px;top:150px;font-size:24px;opacity:0">{e(p.get("kicker"))}</div>
<div class="gar" id="{sid}-h" style="position:absolute;left:150px;top:190px;font-size:56px;opacity:0">{e(p.get("title"))}</div>
<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0">
 <path id="{sid}-p" d="{path}" fill="none" stroke="{RED}" stroke-width="6" stroke-linecap="round" pathLength="100" stroke-dasharray="100 100" stroke-dashoffset="100"/>
</svg>{labs}
<div class="note" id="{sid}-note" style="position:absolute;left:1180px;top:860px;font-size:40px;transform:rotate(-4deg);opacity:0">{e(p.get("note"))}</div>
<div class="tag">SIMPLIFIED ILLUSTRATION · NOT TO SCALE</div>'''
    j = (f'tl.fromTo("#{sid}-k",{{opacity:0}},{{opacity:1,duration:.5}},.2);'
         f'tl.fromTo("#{sid}-h",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.6}},.35);'
         f'tl.fromTo("#{sid}-p",{{attr:{{"stroke-dashoffset":100}}}},{{attr:{{"stroke-dashoffset":0}},duration:{r3(span)},ease:"none"}},{t0});'
         + "".join(f'tl.fromTo("#{sid}-s{k}",{{opacity:0,scale:.6}},{{opacity:1,scale:1,duration:.35}},{r3(t0 + span * k / (n - 1))});' for k in range(len(stops)))
         + (f'tl.fromTo("#{sid}-note",{{opacity:0}},{{opacity:1,duration:.4}},{r3(t0+span+.2)});' if p.get("note") else "") + fade_out(d))
    return h, j, [(s, "whoosh", 1.6), (s + t0, "penline", min(2.0, span))], False


def sc_compare(sid, s, d, b, p, clips):
    items = []
    for it in (p.get("items") or [])[:4]:
        try:
            items.append((str(it[0]), float(str(it[1]).replace(",", "")), str(it[2] if len(it) > 2 else it[1])))
        except (ValueError, IndexError, TypeError):
            pass
    if not items:
        return sc_statement(sid, s, d, b, {"kicker": p.get("kicker"), "text": p.get("title")}, clips)
    mx = max(v for _, v, _ in items) or 1
    hi = max(range(len(items)), key=lambda k: items[k][1])
    rows = "".join(
        f'<div style="position:absolute;left:260px;top:{390+k*170}px;width:1400px"><div class="lab" style="font-size:28px">{e(lab)}</div>'
        f'<div style="display:flex;align-items:center;margin-top:10px"><div id="{sid}-b{k}" style="height:62px;width:{max(30, 1100*v/mx):.0f}px;'
        f'background:{RED if k == hi else "rgba(232,226,211,.75)"};transform-origin:left center"></div>'
        f'<div id="{sid}-v{k}" class="bod" style="font-size:76px;margin-left:28px;opacity:0">{e(disp)}</div></div></div>'
        for k, (lab, v, disp) in enumerate(items))
    h = (f'<div class="lab" id="{sid}-k" style="position:absolute;left:260px;top:190px;opacity:0">{e(p.get("kicker"))}</div>'
         f'<div class="gar" id="{sid}-h" style="position:absolute;left:260px;top:230px;font-size:60px;opacity:0">{e(p.get("title"))}</div>{rows}')
    j = (f'tl.fromTo("#{sid}-k",{{opacity:0}},{{opacity:1,duration:.5}},.2);tl.fromTo("#{sid}-h",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.6}},.3);'
         + "".join(f'tl.fromTo("#{sid}-b{k}",{{scaleX:0}},{{scaleX:1,duration:.8,ease:"power2.out"}},{r3(beat(b, k, d, .9) if k < len(b) else .9 + .6*k)});'
                   f'tl.fromTo("#{sid}-v{k}",{{opacity:0}},{{opacity:1,duration:.4}},{r3((beat(b, k, d, .9) if k < len(b) else .9 + .6*k) + .6)});' for k in range(len(items)))
         + fade_out(d))
    return h, j, [(s + .9, "sub", 2.2)], False


def sc_statement(sid, s, d, b, p, clips):
    txt = e(p.get("text"))
    size = 170 if len(txt) <= 10 else 120 if len(txt) <= 18 else 84
    t = beat(b, p.get("at"), d, .5)
    st = (f'<div id="{sid}-st" class="gar" style="position:absolute;left:0;right:0;top:250px;text-align:center;font-size:46px;font-style:italic;opacity:0">'
          f'<span style="position:relative">{e(p.get("strike"))}<span id="{sid}-sx" style="position:absolute;left:-8px;right:-8px;top:50%;height:4px;background:{RED};transform-origin:left center"></span></span></div>'
          if p.get("strike") else "")
    h = (st + f'<div class="lab" id="{sid}-k" style="position:absolute;left:0;right:0;top:340px;text-align:center;font-size:26px;opacity:0">{e(p.get("kicker"))}</div>'
         f'<div class="gar" id="{sid}-t" style="position:absolute;left:80px;right:80px;top:400px;text-align:center;font-size:{size}px;letter-spacing:.2em;line-height:1.15;opacity:0">{txt}</div>')
    j = ((f'tl.fromTo("#{sid}-st",{{opacity:0}},{{opacity:1,duration:.4}},.2);tl.fromTo("#{sid}-sx",{{scaleX:0}},{{scaleX:1,duration:.45}},.9);' if st else "")
         + f'tl.fromTo("#{sid}-k",{{opacity:0}},{{opacity:1,duration:.4}},{r3(max(.1, t - .4))});'
         f'tl.fromTo("#{sid}-t",{{opacity:0,scale:1.08}},{{opacity:1,scale:1,duration:.35,ease:"power4.out"}},{r3(t)});' + fade_out(d))
    ev = [(s + t, "sub", 2.2)] + ([(s + .9, "penline", .45)] if st else [])
    return h, j, ev, False


def sc_questions(sid, s, d, b, p, clips):
    qs = [q for q in (p.get("items") or []) if q][:3]
    h = "".join(f'<div id="{sid}-q{k}" style="position:absolute;left:220px;top:{260+k*200}px;right:200px;opacity:0"><div class="lab" style="font-size:20px;color:{RED}">Open question 0{k+1}</div>'
                f'<div class="gar" style="font-size:70px;margin-top:12px;line-height:1.15">{e(q)}</div></div>' for k, q in enumerate(qs))
    j = "".join(f'tl.fromTo("#{sid}-q{k}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:.6,ease:"power3.out"}},{r3(beat(b, k, d, .3) if k < len(b) else .3 + 1.2*k)});' for k in range(len(qs))) + fade_out(d)
    return h, j, [], False


def sc_datetime(sid, s, d, b, p, clips):
    tm = e(p.get("time"))
    spaced = " ".join(tm.replace(" ", " "))
    h = (f'<div class="lab" id="{sid}-k" style="position:absolute;left:0;right:0;top:330px;text-align:center;opacity:0">{e(p.get("kicker"))}</div>'
         f'<div id="{sid}-t" class="bod" style="position:absolute;left:0;right:0;top:390px;text-align:center;font-size:160px;letter-spacing:.12em">{spaced}</div>'
         f'<div id="{sid}-l" class="gar" style="position:absolute;left:0;right:0;top:640px;text-align:center;font-size:52px;opacity:0">{e(p.get("line"))}</div>')
    j = (f'tl.fromTo("#{sid}-k",{{opacity:0}},{{opacity:1,duration:.5}},.2);' + typed(f"{sid}-t", .5, min(1.6, d / 3))
         + f'tl.fromTo("#{sid}-l",{{opacity:0,y:12}},{{opacity:1,y:0,duration:.5}},{r3(min(d-1, .6 + min(1.6, d/3)))});' + fade_out(d))
    return h, j, [(s + .5, "type", min(1.6, d / 3))], False


def sc_title(sid, s, d, b, p, clips):
    t = e(p.get("title"))
    size = 190 if len(t) <= 9 else 140 if len(t) <= 14 else 100
    st = (f'<div id="{sid}-st" class="gar" style="position:absolute;left:0;right:0;top:250px;text-align:center;font-size:44px;font-style:italic;opacity:0">'
          f'<span style="position:relative">{e(p.get("strike"))}<span id="{sid}-sx" style="position:absolute;left:-8px;right:-8px;top:50%;height:4px;background:{RED};transform-origin:left center"></span></span></div>'
          if p.get("strike") else "")
    h = st + f'''
<div id="{sid}-k" class="lab" style="position:absolute;left:0;right:0;top:340px;text-align:center;font-size:24px;opacity:0">{e(p.get("kicker"))}</div>
<div id="{sid}-t" class="gar" style="position:absolute;left:0;right:0;top:390px;text-align:center;font-size:{size}px;letter-spacing:.24em;padding-left:.24em;opacity:0">{t}</div>
<div id="{sid}-u" style="position:absolute;left:660px;top:{400+size*1.15:.0f}px;width:600px;height:4px;background:{RED};transform-origin:center"></div>
<div id="{sid}-s" class="gar" style="position:absolute;left:0;right:0;top:{440+size*1.15:.0f}px;text-align:center;font-size:46px;font-style:italic;opacity:0">{e(p.get("subtitle"))}</div>'''
    j = ((f'tl.fromTo("#{sid}-st",{{opacity:0}},{{opacity:1,duration:.4}},.1);tl.fromTo("#{sid}-sx",{{scaleX:0}},{{scaleX:1,duration:.45}},.7);' if st else "")
         + f'tl.fromTo("#{sid}-k",{{opacity:0}},{{opacity:1,duration:.6}},.2);'
         f'tl.fromTo("#{sid}-t",{{opacity:0,scale:1.12}},{{opacity:1,scale:1,duration:.5,ease:"power4.out"}},.1);'
         f'tl.fromTo("#{sid}-u",{{scaleX:0}},{{scaleX:1,duration:.6,ease:"power2.out"}},.6);'
         f'tl.fromTo("#{sid}-s",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.6}},1.0);' + fade_out(d, "#root", .4))
    if str(p.get("kicker") or "").upper().startswith(("PART", "EPILOGUE")):
        h += f'<div id="{sid}-dip" style="position:absolute;inset:0;background:#000;z-index:40"></div>'
        j = f'tl.fromTo("#{sid}-dip",{{opacity:1}},{{opacity:0,duration:.32,ease:"none"}},0);' + j
    return h, j, [(s, "boom", 2.8)] + ([(s + .7, "penline", .45)] if st else []), False


def sc_memorial(sid, s, d, b, p, clips):
    h = f'<div id="{sid}-m" class="gar" style="position:absolute;left:200px;right:200px;top:420px;text-align:center;font-size:62px;font-style:italic;line-height:1.4;color:#F2EDE1;text-shadow:0 2px 18px rgba(0,0,0,.8);opacity:0">{e(p.get("text"))}</div>'
    j = f'tl.fromTo("#{sid}-m",{{opacity:0}},{{opacity:1,duration:1.4}},.4);' + fade_out(d, "#root", .8)
    return h, j, [], False


def sc_endcard(sid, s, d, b, p, clips):
    h = f'''
<div id="{sid}-t" class="gar" style="position:absolute;left:0;right:0;top:400px;text-align:center;font-size:120px;letter-spacing:.3em;padding-left:.3em;opacity:0">WRATH OF EARTH</div>
<div id="{sid}-u" style="position:absolute;left:760px;top:560px;width:400px;height:3px;background:{RED};transform-origin:center"></div>
<div id="{sid}-s" class="lab" style="position:absolute;left:0;right:0;top:610px;text-align:center;font-size:22px;opacity:0">Every fact in this film is sourced in the description</div>'''
    j = (f'tl.fromTo("#{sid}-t",{{opacity:0}},{{opacity:1,duration:1.0}},.3);tl.fromTo("#{sid}-u",{{scaleX:0}},{{scaleX:1,duration:.7}},.9);'
         f'tl.fromTo("#{sid}-s",{{opacity:0}},{{opacity:1,duration:.8}},1.3);' + fade_out(d, "#root", .9))
    return h, j, [], False


def torn(seed, n=26, amp=1.4):
    """jagged clip-path polygon (percent), deterministic per scene"""
    import random
    r = random.Random(seed); pts = []
    for k in range(n): pts.append((100 * k / n, r.uniform(0, amp)))
    for k in range(n): pts.append((100 - r.uniform(0, amp), 100 * k / n))
    for k in range(n): pts.append((100 - 100 * k / n, 100 - r.uniform(0, amp)))
    for k in range(n): pts.append((r.uniform(0, amp), 100 - 100 * k / n))
    return "polygon(" + ",".join(f"{x:.2f}% {y:.2f}%" for x, y in pts) + ")"


NEWS_BG = ("repeating-linear-gradient(90deg,transparent 0 318px,#cfc7b3 318px 352px),"
           "repeating-linear-gradient(0deg,rgba(45,38,30,.20) 0 3px,transparent 3px 14px),#cfc7b3")


def collage_print(i, src, x, y, w, h, rot, t_in, dur, label, seed):
    html = (f'<div id="{i}" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;opacity:0;filter:drop-shadow(0 26px 40px rgba(0,0,0,.55))">'
            f'<div style="position:absolute;inset:0;background:#efe9dc;clip-path:{torn(seed)};padding:18px">'
            f'<video id="{i}-v" class="clip" src="{src}" muted playsinline data-start="{r3(t_in)}" data-duration="{r3(dur - t_in)}" '
            f'style="width:100%;height:100%;object-fit:cover;display:block;clip-path:{torn(seed + 7, 30, .8)}"></video></div>'
            f'<div style="position:absolute;left:-34px;top:-14px;width:190px;height:44px;background:rgba(192,38,34,.86);transform:rotate(-24deg)"></div>'
            f'<div style="position:absolute;right:-30px;bottom:-12px;width:170px;height:42px;background:rgba(192,38,34,.86);transform:rotate(-18deg)"></div>'
            f'<div style="position:absolute;left:26px;bottom:-30px;padding:6px 14px;background:#f4f0e6;color:#1a1714;font-family:WCourier;font-size:19px;transform:rotate(-1.5deg)">{e(label)}</div></div>')
    js = f'tl.fromTo("#{i}",{{y:140,rotation:{rot-7},opacity:0}},{{y:0,rotation:{rot},opacity:1,duration:.5,ease:"power3.out"}},{r3(t_in)});'
    return html, js


def sc_collage(sid, s, d, b, p, clips):
    """Vox-style collage: torn-edge prints taped onto an old newspaper sheet; the 2nd print lands on a later sentence (same timing as print)"""
    seed = sum(map(ord, sid))
    h = (f'<div id="{sid}-np" style="position:absolute;left:-120px;top:-90px;width:2160px;height:1260px;background:{NEWS_BG}">'
         f'<div style="position:absolute;left:300px;top:120px;width:1300px;height:70px;background:rgba(40,34,28,.55)"></div>'
         f'<div style="position:absolute;left:300px;top:205px;width:900px;height:26px;background:rgba(40,34,28,.35)"></div></div>'
         f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse at center,rgba(11,15,16,.25),rgba(11,15,16,.78))"></div>')
    j = f'tl.fromTo("#{sid}-np",{{x:0,rotation:-1.2}},{{x:-60,rotation:-.6,duration:{r3(d)},ease:"none"}},0);'
    ev = [(s, "paper", .8)]
    ah, aj = collage_print(f"{sid}-pa", clips[0], 250, 120, 1060, 640, -2.6, 0, d, p.get("label_a") or "EXHIBIT · A", seed)
    h += ah; j += aj
    if len(clips) > 1:
        t2 = beat(b, 1, d, 0) if len(b) > 1 else d / 2
        t2 = min(max(t2, 2.2), d - 2.2)
        bh, bj = collage_print(f"{sid}-pb", clips[1], 900, 330, 820, 520, 3.2, t2, d, p.get("label_b") or "EXHIBIT · B", seed + 3)
        h += bh; j += bj + f'tl.to("#{sid}-pa",{{x:-110,duration:.5}},{r3(t2)});'
        ev.append((s + t2, "paper", .8))
    lh, lj = lower_third(f"{sid}-lt", p.get("kicker"), p.get("line"), 90, 880, .7, d - .5)
    return h + lh, j + lj + fade_out(d, "#root", .3), ev, True


TYPES = dict(full=sc_full, print=sc_print, print_number=sc_print_number, number=sc_number, document=sc_document, monitor=sc_monitor,
             map=sc_map, compare=sc_compare, statement=sc_statement, questions=sc_questions, datetime=sc_datetime, title=sc_title,
             memorial=sc_memorial, endcard=sc_endcard, collage=sc_collage)
NEEDS_CLIPS = {"full": 1, "print": 1, "print_number": 1, "monitor": 1}


def render_scene(sid, sc, clips):
    """-> (composition html, events)"""
    fn = TYPES["collage" if sc["type"] == "print" and sc.get("mode") == "collage" else sc["type"]]
    h, j, ev, nobg = fn(sid, sc["a"], sc["d"], sc["beats"], sc, clips)
    if not nobg:
        bh, bj = bg(sid, sc["a"], sc["d"], "topo_b.jpg" if sc["type"] in ("map", "compare") else "topo.jpg")
        h, j = bh + h, bj + j
    comp = f'''<template>
<style>{FONTS}{BASE_CSS}</style>
<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080" data-layout-allow-overlap data-layout-allow-overflow>
{h}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{j}
window.__timelines["{sid}"] = tl;
</script>
</template>
'''
    return comp, ev
