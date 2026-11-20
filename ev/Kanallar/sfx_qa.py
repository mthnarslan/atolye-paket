"""SFX kapisi: python sfx_qa.py video.mp4 sfx.json cikti_dir [--tum]
sfx.json: {"whoosh":[t..], "pop":[..], "impact":[..], ...} (mutlak sn).
1) yerel: ust uste/cok yakin SFX (<0.4 sn), dakikadaki yogunluk, video sonundan tasan SFX.
2) Gemini (gemweb) her olayi dinler: olay basina 5 sn ses + olay anindaki kare; duyuluyor mu, zamanlama (gorsel olayla), ses seviyesi, anlatimi bastiriyor mu, uyum.
3) Gemini genel: 3 adet 40 sn kesit (ses + 8 kare): fazla/az SFX, gerekcesiz ses, eksik vurgu, cizirti/klik.
Cikis 0 = gecti; 1 = sorun (rapor sfx_qa.json); 2 = dinletilemedi (kapi kapali say)."""
import json, os, subprocess, sys, concurrent.futures as cf
sys.path.insert(0, "C:/Users/meteh/Kanallar"); import gemweb
MP4, SJ, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
X = json.load(open(SJ, encoding="utf8"))
NE = {"whoosh": "a short whoosh on a chapter-card transition", "pop": "a soft pop when a list row slides in",
      "impact": "a deep bass impact when a red stamp slams onto the image", "click": "a soft click"}
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
D = dur(MP4)
ev = sorted((round(t, 2), k) for k in X for t in X[k])
yerel = []
for i in range(len(ev) - 1):
    if ev[i + 1][0] - ev[i][0] < .4: yerel.append(f"cok yakin: {ev[i]} ve {ev[i + 1]}")
yerel += [f"video disinda: {e}" for e in ev if not 0 <= e[0] < D - .2]
dk = [0] * (int(D // 60) + 1)
for t, _ in ev:
    if 0 <= t < D: dk[int(t // 60)] += 1
yerel += [f"dakika {m}: {c} SFX (fazla)" for m, c in enumerate(dk) if c > 8]
# dalga eslesmesi (matched filter): SFX dosyasi beklenen anda var mi, kac ms kaymis (11-18 olcum: gercek .75-1, sahte <.55)
import numpy as np
from scipy.signal import fftconvolve, butter, sosfiltfilt
HP = butter(4, 150, "highpass", fs=48000, output="sos")  # whoosh/pop/click: onceki impact'in bas kuyrugu eslesmeyi bozmasin (11-18: impact'ten 1.8 sn sonraki whoosh .14 -> .97; 500 Hz gercek whoosh'u .35'e dusurdu, 150 Hz: gercek >=.61, sahte <=.39)
SR = 48000; SFXD = "C:/Users/meteh/.claude/skills/media-use/audio/assets/sfx"
DOSYA = {"pop": "pop", "impact": "impact-bass-1", "whoosh": "whoosh-short", "click": "click-soft"}
ESIK = {"pop": .7, "impact": .5, "whoosh": .45, "click": .5}
def rd(a): return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", *a, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).astype(float)
MIX0 = rd(["-i", MP4]); MIXH = sosfiltfilt(HP, MIX0); olcum = {}
def esles(tpl, t, MIX):
    i0 = max(0, int((t - .3) * SR)); seg = MIX[i0:i0 + int(.6 * SR) + len(tpl)]
    if len(seg) <= len(tpl): return 0.0, 0.0
    c = fftconvolve(seg, tpl[::-1], "valid"); e = np.sqrt(np.clip(fftconvolve(seg ** 2, np.ones(len(tpl)), "valid"), 0, None)) * np.linalg.norm(tpl) + 1e-9
    nc = np.clip(c / np.maximum(e, 1e-3 * np.linalg.norm(tpl) ** 2), -1, 1); k = int(np.argmax(nc)); return float(nc[k]), (k + i0) / SR - t
for tur in sorted({k for _, k in ev}):
    if tur not in DOSYA: continue
    tpl = rd(["-i", f"{SFXD}/{DOSYA[tur]}.mp3"]); a = np.abs(tpl); ix = np.where(a > a.max() * .05)[0]; tpl = tpl[ix[0]:min(ix[-1], ix[0] + int(.15 * SR))]
    M = MIX0 if tur == "impact" else MIXH
    if tur != "impact": tpl = sosfiltfilt(HP, tpl)
    sk = {t: esles(tpl, t, M) for t, k in ev if k == tur}
    iyi = [o for s_, o in sk.values() if s_ >= ESIK[tur]]; med = float(np.median(iyi)) if iyi else 0.0
    for t, (s_, o) in sk.items():
        olcum[(t, tur)] = {"eslesme": round(s_, 3), "kayma_ms": round((o - med) * 1000)}
        if s_ < ESIK[tur]: yerel.append(f"{tur} {t} sn: mixte bulunamadi/duyulmuyor (eslesme {s_:.2f} < {ESIK[tur]})")
        elif abs(o - med) > .04: yerel.append(f"{tur} {t} sn: kayma {(o - med) * 1000:.0f} ms")
def ff(*a): subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
def kes(i, t, k):
    a = max(0, t - 2.5); ff("-ss", f"{a:.2f}", "-t", "5", "-i", MP4, "-vn", "-ac", "1", "-b:a", "96k", f"{OUT}/e{i:02d}.mp3")
    ff("-ss", f"{t + .35:.2f}", "-i", MP4, "-frames:v", "1", "-vf", "scale=640:-1", f"{OUT}/e{i:02d}.jpg")
    return round(t - a, 2)
ofs = {}
with cf.ThreadPoolExecutor(6) as p:
    for i, r in zip(range(len(ev)), p.map(lambda a: kes(a[0], *a[1]), list(enumerate(ev)))): ofs[i] = r
B = [list(range(len(ev)))[j:j + 5] for j in range(0, len(ev), 5)]
import re
OKUNMADI = lambda r: bool(re.search(r"(?:audio|file|clip)s? (?:is |are )?missing|unreadable|could not (?:be )?(?:read|load|play|open|process|decode)|cannot (?:be )?(?:open|read|load)|failed to (?:open|load)|no audio|not (?:provided|attached|accessible)", json.dumps(r), re.I))
# 11-18: gemweb :8790 ses girdisini hic okumuyor (mp3/wav/file hepsi 'CANNOT'); gemweb'i yeniden baslatmak yasak -> ses okunmazsa kendi Gemini API anahtarimiz
sys.path.insert(0, "C:/Users/meteh/.gemini/scripts/documentary_materials")
import base64, mimetypes, requests
def api_json(q, files, model="gemini-3.6-flash"):
    import gemini_keys as gk
    ic = [{"type": "text", "text": q}]
    for f in files:
        b = base64.b64encode(open(f, "rb").read()).decode()
        ic.append({"type": "input_audio", "input_audio": {"data": b, "format": "mp3"}} if f.endswith(".mp3")
                  else {"type": "image_url", "image_url": {"url": f"data:{mimetypes.guess_type(f)[0]};base64,{b}"}})
    import time
    for n in range(12):  # 503 'high demand' Google tarafinda gecici (11-18 aksam): bekleyip ayni modelle tekrar
        if n: time.sleep(min(60, 10 * n))
        pk = gk.pick(model)
        if not pk: raise RuntimeError("Gemini API anahtari kalmadi")
        i, k = pk
        r = requests.post(gk.BASE_URL + "/chat/completions", headers={"Authorization": "Bearer " + k},
                          json={"model": model, "messages": [{"role": "user", "content": ic}]}, timeout=300)
        gk.report(i, r.status_code, model)
        if r.ok:
            v = gemweb.json_al(r.json()["choices"][0]["message"]["content"] or "")
            if v is not None: return v
    raise RuntimeError("Gemini API JSON donmedi")
def ses_sor(q, files):
    # 11-18 aksam: gemweb yamasi da sesi duymadi (0/10, beyin/ders/gemweb-ses-video-yukleme-1118) -> varsayilan dogrudan API; gemweb duzelirse SFXQA_GEMWEB=1
    if os.environ.get("SFXQA_GEMWEB", "1") == "0": return api_json(q, files)  # 18 Kas aksam: gemweb sesi duyuyor (hydrogen high), varsayilan gemweb
    try:
        r = gemweb.sor_json(q, gorseller=files, zaman=300, effort="high")
        if not OKUNMADI(r): return r
    except Exception: pass
    return api_json(q, files)
def soru(grup):
    q = ("You are a strict sound editor reviewing the final mix of a calm German history explainer (narration + quiet dark music bed + sparse sound effects). "
         f"You get {len(grup)} independent 5-second audio clips, then the video frame from the middle of each clip in the same order. "
         "For EACH clip, list every sound effect you actually hear (not speech, not the music bed): approximate time in seconds from clip start, kind (whoosh/pop/click/bass impact/other), "
         "level vs narration (ok/too_loud/too_quiet), masks_speech (yes/no), fits the image and calm tone (yes/no). Also list glitches (click, crackle, distortion, double sound, abrupt cut). "
         "If you hear no sound effect in a clip, return an empty list. Do not guess; report only what you hear. "
         'Return ONLY JSON: {"clips":[{"clip":<1-based>,"sfx":[{"t":s,"kind":"..","level":"..","masks_speech":"yes/no","fits":"yes/no"}],"glitches":[..]}]}')
    files = [f"{OUT}/e{i:02d}.mp3" for i in grup] + [f"{OUT}/e{i:02d}.jpg" for i in grup]
    for _ in range(2):
        try: r = ses_sor(q, files)
        except Exception as e: r = {"hata": str(e)[:200]}; continue
        if not OKUNMADI(r): return r
    return {"hata": "Gemini ses dosyasini okuyamadi: " + json.dumps(r, ensure_ascii=False)[:150]}
# genel kesitler: ilk, orta, son bolum
G = []
for n, a in enumerate([min(30, D * .1), D * .45, max(0, D - 60)]):
    ff("-ss", f"{a:.1f}", "-t", "40", "-i", MP4, "-vn", "-ac", "1", "-b:a", "96k", f"{OUT}/g{n}.mp3")
    ff("-ss", f"{a:.1f}", "-t", "40", "-i", MP4, "-vf", "fps=1/5,scale=480:-1", f"{OUT}/g{n}_%d.jpg")
    inn = [e for e in ev if a <= e[0] < a + 40]
    G.append((n, a, [f"{round(t - a, 1)} s {k}" for t, k in inn]))
def genel(g):
    n, a, inn = g
    q = ("You are a strict sound editor. Attached: a 40-second audio excerpt of the final mix of a German history explainer, then 8 frames (one every 5 s). "
         f"Our SFX list for this excerpt (time in excerpt, type): {inn or 'none'}. "
         "Judge: amount (too_many/ok/too_few for a calm documentary), unexplained (any sound effect that has no visual reason or is not in our list), "
         "missing (visual hits that clearly needed a sound but had none), glitches (clicks, crackles, pops, distortion, abrupt cuts, music bed jumps), "
         "music_bed (ok/too_loud/too_quiet/odd), overall 0-10. "
         'Return ONLY JSON: {"amount":"..","unexplained":[..],"missing":[..],"glitches":[..],"music_bed":"..","overall":n,"note":".."}')
    fs = [f"{OUT}/g{n}.mp3"] + [f"{OUT}/g{n}_{k}.jpg" for k in range(1, 9) if os.path.exists(f"{OUT}/g{n}_{k}.jpg")]
    for _ in range(2):
        try: r = ses_sor(q, fs)
        except Exception as e: r = {"hata": str(e)[:200]}; continue
        if not OKUNMADI(r): return {"kesit_bas": round(a, 1), **r}
    return {"kesit_bas": round(a, 1), "hata": "genel kesit dinlenemedi: " + json.dumps(r, ensure_ascii=False)[:150]}
with cf.ThreadPoolExecutor(4) as p:
    R = list(p.map(soru, B)); GR = list(p.map(genel, G))
olay, kotu, hata, uyari = [], [], [], []
for grup, r in zip(B, R):
    if "hata" in r: hata.append(r["hata"]); continue
    m = {int(c.get("clip", 0)) - 1: c for c in r.get("clips", []) if str(c.get("clip", "")).isdigit()}
    for n, i in enumerate(grup):
        c = m.get(n)
        if c is None: hata.append(f"olay {i} yanitsiz"); continue
        sx = c.get("sfx") or []
        yak = [x for x in sx if isinstance(x.get("t"), (int, float)) and abs(x["t"] - ofs[i]) <= .6]
        e = {"t": ev[i][0], "tur": ev[i][1], **olcum.get(ev[i], {}), "gemini_duydu": bool(yak), "gemini": c}; olay.append(e)
        sorun = [f"{k}={x.get(k)}" for x in yak for k in ("level", "masks_speech", "fits") if x.get(k) not in ("ok", "no" if k == "masks_speech" else "yes")]
        sorun += [f"glitch: {g}" for g in c.get("glitches") or []]
        if not yak: uyari.append(f"{ev[i][1]} {ev[i][0]} sn: Gemini kor dinlemede duymadi (yerel eslesme {olcum.get(ev[i], {}).get('eslesme')}) -> elle dinle")
        if sorun: kotu.append({"t": ev[i][0], "tur": ev[i][1], "sorun": sorun})
for g in GR:
    if "hata" in g: hata.append(g["hata"])
    elif g.get("amount") != "ok" or g.get("glitches") or g.get("unexplained") or g.get("music_bed") != "ok" or (g.get("overall") or 0) < 7: kotu.append({"genel": g})
rap = {"video": MP4, "sure": round(D, 1), "olay": len(ev), "dakika_sfx": dk, "yerel": yerel, "kotu": kotu, "uyari": uyari, "hata": hata, "olaylar": olay, "genel": GR}
json.dump(rap, open(f"{OUT}/sfx_qa.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("SFX QA", len(ev), "olay | yerel", len(yerel), "| kotu", len(kotu), "| uyari", len(uyari), "| dinlenemedi", len(hata))
for k in yerel + [json.dumps(k, ensure_ascii=False)[:300] for k in kotu] + hata: print(" -", k)
for k in uyari: print(" ? ", k)
sys.exit(2 if hata else 1 if (yerel or kotu) else 0)
