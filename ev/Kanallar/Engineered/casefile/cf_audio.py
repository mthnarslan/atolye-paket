"""Audio for a [t0,t1] film window: voice (-16 LUFS), per-section synthesized drone ducked under speech (sidechain-like), SFX trimmed per the style notes."""
import subprocess
import numpy as np
from scipy.signal import lfilter
from cf_common import *

SR = 48000
ROOTS = [73.42, 82.41, 65.41, 87.31, 73.42, 98.0, 65.41]      # D2 E2 C2 F2 ... one drone root per section


def load(path, ss=None, dur=None):
    a = ["-ss", f"{ss:.3f}", "-t", f"{dur:.3f}"] if ss is not None else []
    raw = subprocess.run(["ffmpeg", "-v", "error", *a, "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float32)


def lp(x, a):
    return lfilter([a], [1, a - 1], x).astype(np.float32)


def env(n, att, rel):
    t = np.arange(n) / SR
    return np.clip(np.minimum(1, t / max(att, 1e-3)) * np.minimum(1, (n / SR - t) / max(rel, 1e-3)), 0, 1).astype(np.float32)


def db(x):
    return 10 ** (x / 20)


def synth(kind, d, rng):
    n = int(SR * d); w = rng.standard_normal(n).astype(np.float32); t = np.arange(n) / SR
    if kind == "pen":
        return lp(w - lp(w, .25), .6) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 7.5 * t + rng.uniform(0, 6)))) * env(n, .03, .08) * .5
    b = lp(w - lp(w, .02), .18)                           # paper
    return b * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5 * .9


def build(items, events, t0, t1, voice_n, out, work):
    rng = np.random.default_rng(11); N = int((t1 - t0) * SR)
    voice = np.zeros(N, np.float32)
    v = load(voice_n, ss=t0, dur=t1 - t0) if t0 < 1e5 else np.zeros(0, np.float32)
    voice[:min(N, len(v))] = v[:N]
    tt = np.arange(N) / SR + t0
    # music: one drone per section, equal-power crossfades of 3 s
    music = np.zeros(N, np.float32)
    bounds = sorted({(it["sec"], it["a"]) for it in items}, key=lambda x: x[1]); first = {}
    for s, a in bounds: first.setdefault(s, a)
    ss = sorted(first.items())
    for k, (s, a) in enumerate(ss):
        b = ss[k + 1][1] if k + 1 < len(ss) else 1e9
        f0 = ROOTS[s % len(ROOTS)]
        sig = np.zeros(N, np.float32)
        for f, g in ((f0, .5), (f0 * 1.5, .32), (f0 * 2, .16), (f0 * 2.38, .10)):
            sig += g * np.sin(2 * np.pi * f * tt + .3 * np.sin(2 * np.pi * .07 * tt)) * (.75 + .25 * np.sin(2 * np.pi * (.05 + f / 4000) * tt))
        wind = lp(rng.standard_normal(N).astype(np.float32), .004); wind /= np.abs(wind).max() + 1e-9
        sig += .5 * wind * (.6 + .4 * np.sin(2 * np.pi * .11 * tt))
        win = np.clip(np.minimum((tt - (a - 1.5)) / 3, (b + 1.5 - tt) / 3), 0, 1) if k else np.clip((b + 1.5 - tt) / 3, 0, 1)
        music += sig * win.astype(np.float32) * (1.0 + .25 * (s % 3))
    music /= np.abs(music).max() + 1e-9
    lvl = np.sqrt(lp(voice ** 2, .0008)); lvl = lvl / (lvl.max() + 1e-9)
    duck = lp(np.interp(lvl, [0, .06, .3], [db(-19), db(-24), db(-27)]).astype(np.float32), .0004)
    music *= duck
    # memorial: music drops ~18 dB
    for it in items:
        if it.get("kind") == "memorial":
            m = (tt >= it["a"]) & (tt < it["b"]); music[m] *= db(-18)
    lib = {k: load(SFX / f"{k}.mp3") for k in ("typing", "impact-bass-1", "impact-bass-2", "whoosh-cinematic", "glitch-1")}
    nm = {k: a / (np.abs(a).max() + 1e-9) for k, a in lib.items()}
    fx = np.zeros(N, np.float32)

    def cut(k, d, att=.005, rel=.06):
        a = nm[k][:int(d * SR)].copy(); return a * env(len(a), att, min(rel, d / 2))

    def add(t, sig, g):
        i = int((t - t0) * SR)
        if i >= N or i + len(sig) <= 0: return
        s0 = max(0, -i); n = min(len(sig) - s0, N - max(i, 0)); fx[max(i, 0):max(i, 0) + n] += sig[s0:s0 + n] * db(g)
    for t, kind, d in events:
        if not (t0 - 3 <= t < t1): continue
        if kind == "paper": add(t, synth("paper", .8, rng), -19)
        elif kind == "paper_soft": add(t, synth("paper", .8, rng), -26)
        elif kind == "pen": add(t, synth("pen", .75, rng), -17)
        elif kind == "penline": add(t, synth("pen", .45, rng), -18)
        elif kind == "type": add(t, cut("typing", d), -27)
        elif kind == "sub": add(t, cut("impact-bass-1", 2.2, .005, 1.0), -15)
        elif kind == "boom": add(t, nm["impact-bass-2"][:int(2.8 * SR)] * env(int(min(2.8 * SR, len(nm["impact-bass-2"]))), .005, 1.2), -11)
        elif kind == "whoosh": add(t, cut("whoosh-cinematic", d, .05, .5), -22)
        elif kind == "glitch": add(t, cut("glitch-1", d), -30)
    mix = voice + music + fx
    raw = work / "_mix.f32"; mix.astype(np.float32).tofile(raw)
    ffmpeg(["-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw), "-af", "alimiter=limit=0.85:level=false,pan=stereo|c0=c0|c1=c0", "-c:a", "pcm_s16le", str(out)])
    raw.unlink()


def voice_norm(voice, out):
    if not out.exists():
        ffmpeg(["-i", str(voice), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(out)])
    return out
