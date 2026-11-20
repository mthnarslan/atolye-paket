"""Graphics: our own cards drawn with PIL (frame generators piped to ffmpeg) + static mode assets (monitor, newspaper, tear mask,
chrome, lower-thirds). All layout is in 1920x1080 design pixels; px() scales by S (0.5 for the 960x540 preview)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from cf_common import *

S = 1.0
FD = ASSETS / "fonts"
FONT = {"gar": "GARA.TTF", "garb": "GARABD.TTF", "gari": "GARAIT.TTF", "bod": "BOD_R.TTF", "bahn": "bahnschrift.ttf", "cour": "cour.ttf", "courb": "cour.ttf", "script": "segoesc.ttf"}
_fc = {}


def setscale(s):
    global S
    S = s


def px(x):
    return int(round(x * S))


def font(name, size):
    k = (name, px(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(str(FD / FONT[name]), max(6, px(size)))
    return _fc[k]


def tlen(s, f, tr=0):
    return sum(f.getlength(c) for c in s) + px(tr) * max(0, len(s) - 1) if tr else f.getlength(s)


def put(d, x, y, s, name, size, fill, tr=0, al="l"):
    """Text at design coords; tr = tracking in design px; al l/m/r. Returns drawn width (device px)."""
    f = font(name, size); w = tlen(s, f, tr)
    x0 = px(x) - (w / 2 if al == "m" else w if al == "r" else 0)
    if not tr:
        d.text((x0, px(y)), s, font=f, fill=fill)
    else:
        for c in s:
            d.text((x0, px(y)), c, font=f, fill=fill); x0 += f.getlength(c) + px(tr)
    return w


def ease(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


def sq(W=None, H=None):
    return (px(W or 1920), px(H or 1080))


# ------------------------------------------------------------------ topo background
def topo_path():
    p = ASSETS / "topo.jpg"
    if not p.exists():
        W, H = 2600, 1500
        rng = np.random.default_rng(7)
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); f = np.zeros((H, W), np.float32)
        for o in range(4):
            fr = 0.00028 * 2.1 ** o
            for _ in range(3):
                a, b, ph = rng.uniform(-1, 1, 3) * [1, 1, 6.28]
                f += np.sin((x * a + y * b) * fr * 6.28 + ph) / (2.3 ** o)
        f = (f - f.min()) / (f.max() - f.min()); band = (f * 30) % 1.0
        line = np.clip(1 - np.minimum(band, 1 - band) / 0.06, 0, 1); major = (np.floor(f * 30) % 5 == 0) & (line > 0)
        img = np.full((H, W, 3), INK, np.float32); alpha = line * np.where(major, .55, .26)
        img = img * (1 - alpha[..., None]) + np.array((120, 132, 128), np.float32) * alpha[..., None]
        g = ((x % 130) < 1.5) | ((y % 130) < 1.5); img[g] = img[g] * .85 + np.array((60, 70, 70)) * .15
        v = 1 - .75 * np.clip(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2, 0, 1.6) / 1.6
        img *= v[..., None]; img += rng.normal(0, 3.0, (H, W, 1))
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6)).save(p, quality=90)
    return p


DRIFT = 3.0   # px/s of film time; ping-pong inside the 680 x 420 px of spare topo image


def drift_xy(t):
    rx, ry = 680, 420
    tri = lambda v, r: r - abs(math.fmod(v, 2 * r) - r)
    return tri(DRIFT * t, rx), tri(DRIFT * .45 * t + 60, ry)


_topo = {}


def topo_crop(t):
    k = S
    if k not in _topo:
        _topo[k] = np.asarray(Image.open(topo_path()).convert("RGB").resize((px(2600), px(1500)), Image.BILINEAR))
    x, y = drift_xy(t); x, y = px(x), px(y); a = _topo[k]
    return Image.fromarray(a[y:y + px(1080), x:x + px(1920)])


# ------------------------------------------------------------------ paper
def paper_img(w, h, seed=1, pad=0, shadow=True):
    """Cream paper with fibre noise and a drop shadow; returns RGBA of (w+2pad, h+2pad) device px."""
    rng = np.random.default_rng(seed)
    base = np.array(PAPER, np.float32) + rng.normal(0, 3, (h, w, 1)) + np.linspace(-6, 4, h)[:, None, None]
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow and pad:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((pad, pad + px(26), pad + w, pad + h + px(26)), fill=(0, 0, 0, 150))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px(22))))
    img.paste(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA"), (pad, pad))
    return img


def over(base, layer, x, y):
    """alpha_composite with clipping at frame edges."""
    x, y = int(x), int(y)
    if x >= base.width or y >= base.height or x + layer.width <= 0 or y + layer.height <= 0:
        return
    sx, sy = max(0, -x), max(0, -y)
    l = layer.crop((sx, sy, min(layer.width, base.width - x), min(layer.height, base.height - y)))
    base.alpha_composite(l, (max(0, x), max(0, y)))


def place(frame, layer, cx, cy, ang=0.0, alpha=1.0):
    if ang:
        layer = layer.rotate(ang, Image.BICUBIC, expand=True)
    if alpha < 1:
        a = layer.getchannel("A").point(lambda v: int(v * alpha)); layer = layer.copy(); layer.putalpha(a)
    over(frame, layer, cx - layer.width / 2, cy - layer.height / 2)


def ring_points(box, prog, seed=3):
    """Hand-drawn ellipse around box=(x0,y0,x1,y1), 1.08 turns, drawn up to prog (0..1)."""
    r = random.Random(seed); x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 * 1.1, (y1 - y0) / 2 * 1.35
    a0, n = math.radians(-150 + r.uniform(-20, 20)), 90
    ph = r.uniform(0, 6)
    pts = []
    for i in range(int(n * prog) + 1):
        u = i / n; a = a0 + u * 2 * math.pi * 1.08; k = 1 + .05 * math.sin(3 * a + ph) + .06 * u
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts


def pen_line(d, pts, w=5):
    if len(pts) > 1:
        d.line(pts, fill=RED + (235,), width=max(2, px(w)), joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse((p[0] - px(w) / 2, p[1] - px(w) / 2, p[0] + px(w) / 2, p[1] + px(w) / 2), fill=RED + (235,))


# ------------------------------------------------------------------ cards: each returns (draw(t, frame_rgba), events)
def c_document(c, D, t0):
    lines = [c["header"].upper()[:46]] + list(c["lines"])
    rings, strike = [i + 1 for i in c.get("rings", [])], [i + 1 for i in c.get("strike", [])]
    W, M, LH = 980, 40, 62
    Hh = 190 + LH * len(c["lines"]) + 90
    note = c.get("note")
    pad = px(60); pw, ph = px(W), px(Hh)
    base = paper_img(pw, ph, seed=len(lines), pad=pad)
    k = min(1.0, (D - 1.6) / (0.5 + .045 * sum(len(x) for x in lines) + .75 * len(rings) + .5 * len(strike) + 1.0))
    k = max(.35, k); cps = 30 / k
    ev, tm, starts = [(0.0, "paper", .8)], .45, []
    for i, s in enumerate(lines):
        dur = len(s) / cps + .1; starts.append((tm, dur)); ev.append((tm, "type", min(dur, 3.5))); tm += dur + .12
    rt = {}
    for i in strike:
        rt[i] = ("s", tm, .45 * k + .1); ev.append((tm, "penline", .45)); tm += .55 * k
    for i in rings:
        rt[i] = ("r", tm + .2, .7); ev.append((tm + .2, "pen", .75)); tm += .2 + .85 * k
    note_t = tm + .1
    ang = random.Random(h(c)).uniform(-2.2, 2.2)

    def draw(t, fr):
        im = base.copy(); d = ImageDraw.Draw(im)
        ox, oy = pad + px(70), pad + px(56)
        for i, s in enumerate(lines):
            st, du = starts[i]
            n = len(s) if t >= st + du else int(max(0, t - st) / du * len(s)) if t > st else 0
            y = 0 if i == 0 else 78 + (i - 1) * LH + 22
            sz, nm, col = (21, "cour", (40, 34, 28)) if i == 0 else (29, "cour", (26, 23, 20))
            if i == 0:
                put(d, 0, 0, "", nm, sz, col)
            xx, yy = ox, oy + px(y)
            f = font(nm, sz)
            if n:
                d.text((xx, yy), s[:n], font=f, fill=col)
            if i == 0 and t > st:
                d.line((ox, oy + px(48), ox + pw - px(140), oy + px(48)), fill=(26, 23, 20), width=px(2))
            if i in rt:
                kd, rs, rd = rt[i]; wtxt = f.getlength(s); u = (t - rs) / rd
                if kd == "s" and u > 0:
                    d.line((xx, yy + px(18), xx + wtxt * min(1, u), yy + px(18)), fill=RED + (240,), width=px(5))
                if kd == "r" and u > 0:
                    pen_line(d, ring_points((xx - px(10), yy + px(2), xx + wtxt + px(10), yy + px(34)), min(1, u), seed=i + len(s)))
        put(d, 60 + 70, 60 + Hh - 56, "ILLUSTRATIVE LAYOUT", "bahn", 16, (107, 98, 88), tr=6)
        if note and t > note_t:
            u = ease((t - note_t) / .4)
            tmp = Image.new("RGBA", im.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(tmp)
            put(dd, 60 + W - 250 - len(note) * 6, 60 + Hh - 150, note, "script", 38, RED + (int(235 * u),))
            im.alpha_composite(tmp.rotate(6, Image.BICUBIC, center=(px(60 + W - 250), px(60 + Hh - 130))))
        u = ease(t / .55)
        im = im.resize((int(im.width * 1.3), int(im.height * 1.3)), Image.BILINEAR)
        place(fr, im, px(960), px(540) + px(430) * (1 - u) - px(14) * min(1, max(0, (t - D + .4) / .4)) * 3, ang - 6 * (1 - u), alpha=min(1, max(0, (D - t) / .3)) if t > D - .3 else 1)
    return draw, ev


def c_number(c, D, t0):
    val = str(c["value"]); mv = re.match(r"^[\d,]+(\.\d+)?$", val)
    tgt = float(val.replace(",", "")) if mv else None
    dec = len(val.split(".")[1]) if mv and "." in val else 0

    def draw(t, fr):
        d = ImageDraw.Draw(fr); a = int(255 * ease(t / .5))
        put(d, 960, 270, str(c.get("kicker") or "").upper(), "bahn", 26, PAPER + (a,), tr=9, al="m")
        u = ease((t - .25) / 1.0)
        if tgt is not None:
            v = tgt * u; s = f"{v:,.{dec}f}" if "," in val or v >= 1000 else f"{v:.{dec}f}"
        else:
            s = val
        w = put(d, 960, 330, s, "bod", 260, PAPER + (int(255 * ease(t / .3)),), al="m")
        unit = str(c.get("unit") or "")
        if unit:
            put(d, 960, 640, unit.upper(), "gar", 64, RED + (a,), tr=18, al="m")
        lw = px(520) * ease((t - 1.1) / .45)
        d.rectangle((px(960) - lw / 2, px(730), px(960) + lw / 2, px(734)), fill=RED + (255,))
        put(d, 960, 760, str(c["label"]).upper(), "bahn", 30, PAPER + (int(255 * ease((t - 1.2) / .5)),), tr=8, al="m")
        if c.get("source"):
            put(d, 960, 830, "SOURCE · " + str(c["source"]).upper(), "bahn", 18, PAPER + (int(150 * ease((t - 1.6) / .5)),), tr=6, al="m")
    return draw, [(.2, "sub", 2.2)]


def c_datetime(c, D, t0):
    txt = " ".join(str(c["text"]).upper()) if len(str(c["text"])) < 14 else str(c["text"]).upper()
    ty = min(1.6, D * .4)

    def draw(t, fr):
        d = ImageDraw.Draw(fr)
        put(d, 960, 290, str(c.get("kicker") or "").upper(), "bahn", 26, PAPER + (int(255 * ease(t / .5)),), tr=9, al="m")
        n = int(min(1, max(0, (t - .3) / ty)) * len(txt))
        sz = min(190, 190 * 1500 / max(1, tlen(txt, font("gar", 190), 14) / S)); w = tlen(txt, font("gar", sz), 14)
        x0 = 960 - w / S / 2
        put(d, x0, 380 + (190 - sz) * .4, txt[:n], "gar", sz, PAPER + (255,), tr=14, al="l")
        if t > .3 + ty and c.get("place"):
            a = int(255 * ease((t - .3 - ty) / .5))
            d.rectangle((px(960 - 140), px(640), px(960 + 140), px(643)), fill=RED + (a,))
            put(d, 960, 670, str(c["place"]), "gar", 54, PAPER + (a,), tr=4, al="m")
    return draw, [(.3, "type", ty)]


def c_map(c, D, t0):
    r = random.Random(h(c)); sx, sy, ex, ey = 300, r.randint(640, 760), 1620, r.randint(300, 420)
    cx1, cy1, cx2, cy2 = 700, sy - 260, 1200, ey + 320
    pts = []
    for i in range(61):
        u = i / 60; b = [(1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u ** 2 * (1 - u), u ** 3]
        pts.append((px(b[0] * sx + b[1] * cx1 + b[2] * cx2 + b[3] * ex), px(b[0] * sy + b[1] * cy1 + b[2] * cy2 + b[3] * ey)))

    def draw(t, fr):
        d = ImageDraw.Draw(fr); u = ease((t - .5) / max(1.5, D * .5))
        for q in range(0, 1920, 192):
            d.line((px(q), 0, px(q), px(1080)), fill=(90, 100, 100, 30), width=1)
        seg = pts[:int(len(pts) * u) + 1]
        for w, a in ((14, 40), (8, 90), (5, 255)):
            if len(seg) > 1: d.line(seg, fill=RED + (a,), width=px(w), joint="curve")
        for (x, y, lab, al) in ((sx, sy, c["from"], "l"), (ex, ey, c["to"], "r")):
            d.ellipse((px(x) - px(10), px(y) - px(10), px(x) + px(10), px(y) + px(10)), outline=PAPER + (255,), width=px(3))
            put(d, x + (-20 if al == "r" else 20) * 0, y + 24, str(lab).upper(), "bahn", 26, PAPER + (int(255 * ease(t / .6)),), tr=7, al="m")
        if c.get("label") or c.get("distance"):
            a = int(255 * ease((t - .5 - max(1.5, D * .5)) / .5))
            put(d, 960, 130, str(c.get("distance") or ""), "bod", 120, PAPER + (a,), al="m")
            put(d, 960, 280, str(c.get("label") or "").upper(), "bahn", 26, PAPER + (a,), tr=9, al="m")
    return draw, [(0, "whoosh", 1.6)]


def wrap(s, f, maxw):
    out, cur = [], ""
    for wd in s.split():
        if f.getlength((cur + " " + wd).strip()) > maxw and cur:
            out.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    return out + [cur]


def c_quote(c, D, t0):
    f = font("gari", 64); lines = wrap("“" + c["text"].strip() + "”", f, px(1300)); by = str(c.get("by") or "")
    hh = len(lines) * 84

    def draw(t, fr):
        d = ImageDraw.Draw(fr); y0 = 540 - hh / 2 - 30
        bar = px(hh) * ease(t / .6)
        d.rectangle((px(250), px(y0), px(255), px(y0) + bar), fill=RED + (255,))
        for i, s in enumerate(lines):
            a = int(255 * ease((t - .2 - i * .25) / .5)); d.text((px(300), px(y0 + i * 84)), s, font=f, fill=PAPER + (a,))
        if by:
            put(d, 300, y0 + hh + 24, "— " + by.upper(), "bahn", 24, PAPER + (int(200 * ease((t - 1.0) / .5)),), tr=8)
    return draw, [(0.1, "paper", .8)]


def c_compare(c, D, t0):
    a, b = c["a"], c["b"]; mx = max(float(a["value"]), float(b["value"]))

    def draw(t, fr):
        d = ImageDraw.Draw(fr)
        put(d, 960, 190, str(c.get("title") or "").upper(), "bahn", 28, PAPER + (int(255 * ease(t / .5)),), tr=9, al="m")
        for k, (it, y, col) in enumerate(((a, 360, PAPER), (b, 600, RED))):
            u = ease((t - .5 - k * .6) / 1.0); v = float(it["value"]); wmax = 1050
            d.rectangle((px(300), px(y + 60), px(300 + wmax * v / mx * u), px(y + 100)), fill=col + (255,))
            put(d, 300, y - 20, str(it["label"]).upper(), "bahn", 26, PAPER + (int(255 * ease((t - .4 - k * .6) / .4)),), tr=7)
            s = f"{v * u:,.0f}" if v >= 10 else f"{v * u:.1f}"
            put(d, 300 + wmax * v / mx * u + 24, y + 30, s + " " + str(c.get("unit") or ""), "bod", 70, PAPER + (255,))
    return draw, [(.5, "sub", 2.2)]


def c_section(c, D, t0):
    def draw(t, fr):
        d = ImageDraw.Draw(fr); a = int(255 * ease(t / .5))
        if c.get("tease"):
            u = ease((t - .5) / .5)
            w = put(d, 960, 270, c["tease"], "gari", 52, PAPER + (int(200 * ease(t / .4)),), tr=2, al="m")
            lw = tlen(c["tease"], font("gari", 52), 2) * u
            d.line((px(960) - lw / 2, px(300), px(960) + lw / 2, px(300)), fill=RED + (255,), width=px(5))
        put(d, 960, 380, str(c.get("kicker") or "").upper(), "bahn", 28, PAPER + (a,), tr=14, al="m")
        s = str(c["title"]).upper(); size = 150 if len(s) <= 14 else 110 if len(s) <= 22 else 80
        put(d, 960, 440, s, "gar", size, PAPER + (int(255 * ease((t - .1) / .4)),), tr=size * .16, al="m")
        d.rectangle((px(960) - px(300) * ease((t - .6) / .6), px(660), px(960) + px(300) * ease((t - .6) / .6), px(664)), fill=RED + (255,))
    return draw, [(0, "boom", 2.8)]


def c_memorial(c, D, t0):
    f = font("gari", 54); lines = wrap(c["text"], f, px(1400))

    def draw(t, fr):
        d = ImageDraw.Draw(fr); a = int(255 * ease((t - .5) / 1.5) * (1 - ease((t - D + 1.0) / .9)))
        for i, s in enumerate(lines):
            d.text((px(960) - f.getlength(s) / 2, px(470 + i * 76 - (len(lines) - 1) * 38)), s, font=f, fill=PAPER + (a,))
    return draw, []


def c_endcard(c, D, t0):
    def draw(t, fr):
        d = ImageDraw.Draw(fr); a = int(255 * ease(t / 1.0) * (1 - ease((t - D + .9) / .8)))
        put(d, 960, 400, "WRATH OF EARTH", "gar", 120, PAPER + (a,), tr=22, al="m")
        d.rectangle((px(660), px(560), px(1260), px(563)), fill=RED + (a,))
        put(d, 960, 610, "Every fact in this film is sourced in the description.", "gari", 40, PAPER + (int(a * .85),), al="m")
    return draw, []


CARDS = dict(document=c_document, number=c_number, datetime=c_datetime, map=c_map, quote=c_quote, compare=c_compare,
             section=c_section, memorial=c_memorial, endcard=c_endcard)
DARK = {"memorial", "endcard"}   # solid ink instead of the drifting topo


def card_frames(kind, spec, D, t_abs):
    """Generator of raw RGB frame bytes for a full-frame card of D seconds starting at film time t_abs."""
    draw, ev = CARDS[kind](spec, D, t_abs); n = int(round(D * FPS))
    def gen():
        for i in range(n):
            t = i / FPS
            fr = Image.new("RGBA", sq(), INK + (255,)) if kind in DARK else topo_crop(t_abs + t).convert("RGBA")
            draw(t, fr); yield fr.convert("RGB").tobytes()
    return gen(), ev


# ------------------------------------------------------------------ static assets (PNG) per scale
def asset(name, make):
    p = HERE / "work" / "_assets" / f"{name}_{S}.png"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True); make().save(p)
    return str(p)


def chrome_png(label):
    def mk():
        im = Image.new("RGBA", sq(), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = PAPER + (140,)
        for (x, y, sx, sy) in ((60, 60, 1, 1), (1860, 60, -1, 1), (60, 1020, 1, -1), (1860, 1020, -1, -1)):
            d.line((px(x), px(y), px(x + 46 * sx), px(y)), fill=c, width=px(2)); d.line((px(x), px(y), px(x), px(y + 46 * sy)), fill=c, width=px(2))
        d.ellipse((px(84), px(80), px(95), px(91)), fill=RED + (255,))
        put(d, 108, 74, label.upper()[:60], "bahn", 17, PAPER + (160,), tr=5)
        put(d, 1836, 70, "WRATH OF EARTH", "gar", 24, PAPER + (110,), tr=9, al="r")
        return im
    return asset("chrome_" + h(label), mk)


def lt_png(kicker, line, plate=False):
    def mk():
        k, l = kicker.upper(), line
        tw = max(tlen(k, font("bahn", 20), 6), tlen(l, font("gar", 44), 2)); full = px(26) + tw + px(28); w = full + px(60)
        im = Image.new("RGBA", (int(w), px(140)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for x in range(int(w)):
            a = int((248 if plate else 210) * (1 - max(0, (x - full) / (w - full)))); d.line((x, 0, x, px(140)), fill=(11, 15, 16, a))
        im = im.filter(ImageFilter.GaussianBlur(px(2))); d = ImageDraw.Draw(im)
        d.rectangle((0, px(8), px(3), px(130)), fill=RED + (255,))
        put(d, 26, 16, k, "bahn", 20, PAPER + (190,), tr=6)
        d.line((px(26), px(52), px(26) + tlen(l, font("gar", 44), 2) * .9, px(52)), fill=PAPER + (110,), width=1)
        put(d, 26, 62, l, "gar", 44, PAPER + (255,), tr=2)
        return im
    return asset("lt_" + h(kicker, line, plate), mk)


def monitor_assets():
    def bg():
        im = Image.new("RGBA", sq(), INK + (255,)); d = ImageDraw.Draw(im)
        for i in range(25):
            d.line((px(960 + (i - 12) * 40), px(560), px(960 + (i - 12) * 260), px(1080)), fill=RED + (70,), width=max(1, px(1.5)))
        for k in range(1, 10):
            d.line((0, px(560 + k * k * 7), px(1920), px(560 + k * k * 7)), fill=RED + (55,), width=max(1, px(1.5)))
        glow = Image.new("RGBA", sq(), (0, 0, 0, 0)); ImageDraw.Draw(glow).rectangle((px(440), px(130), px(1480), px(770)), fill=(150, 195, 205, 70))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(px(50))))
        d.rectangle((px(930), px(764), px(990), px(884)), fill=(18, 21, 22, 255)); d.rounded_rectangle((px(840), px(880), px(1080), px(894)), px(4), fill=(18, 21, 22, 255))
        return im

    def bez():
        im = Image.new("RGBA", sq(), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rectangle((px(460), px(150), px(1460), px(750)), outline=(21, 25, 26, 255), width=px(14))
        d.rectangle((px(446), px(136), px(1474), px(764)), outline=(200, 220, 225, 70), width=px(2))
        return im
    return asset("mon_bg", bg), asset("mon_bezel", bez)


def newspaper_png():
    def mk():
        rng = random.Random(5); W, H = px(2100), px(1180)
        a = np.array((196, 184, 156), np.float32) + np.random.default_rng(2).normal(0, 4, (H, W, 1))
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im)
        for col in range(7):
            x = px(40 + col * 295)
            for ln in range(0, 62):
                y = px(70 + ln * 17); w = px(250 * rng.uniform(.5, 1))
                d.rectangle((x, y, x + w, y + px(5)), fill=(70, 62, 50, 120))
            put(d, 40 + col * 295, 8 + (col % 3) * 4, rng.choice(["STORM", "WARNING", "TORNADO", "DAMAGE", "RADAR"]), "garb", 40, (50, 44, 36, 170))
        v = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(v).rectangle((0, 0, W, H), outline=(20, 15, 8, 200), width=px(140))
        im.alpha_composite(v.filter(ImageFilter.GaussianBlur(px(110))))
        return im.convert("RGB")
    return asset("news", mk)


def tear_mask(w, h):
    def mk():
        rng = random.Random(w * 7 + h); m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m); j = max(3, px(9))
        pts = [(rng.randint(0, j), rng.randint(0, j))]
        for x in range(0, w, max(4, px(14))): pts.append((x, rng.randint(0, j)))
        for y in range(0, h, max(4, px(14))): pts.append((w - rng.randint(0, j), y))
        for x in range(w, 0, -max(4, px(14))): pts.append((x, h - rng.randint(0, j)))
        for y in range(h, 0, -max(4, px(14))): pts.append((rng.randint(0, j), y))
        d.polygon(pts, fill=255)
        return m
    return asset(f"tear_{w}_{h}", mk)


def tape_png(box_w, box_h, cx, cy, ang):
    def mk():
        im = Image.new("RGBA", sq(), (0, 0, 0, 0))
        for sx, sy in ((-1, -1), (1, 1)):
            t = Image.new("RGBA", (px(150), px(44)), RED + (200,)); t = t.rotate(-45 * sx * sy + ang, Image.BICUBIC, expand=True)
            over(im, t, px(cx + sx * box_w / 2) - t.width / 2, px(cy + sy * box_h / 2) - t.height / 2)
        return im
    return asset(f"tape_{box_w}_{box_h}_{cx}_{cy}_{ang}", mk)
