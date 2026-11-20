---
tur: konu
aciklama: ZERO PULSE new-episode steps, pre-delivery checks and code-level gotchas in SkullStudio (learned 2026-10-29)
kaynak: auto-memory C--Users-meteh-Kanallar-ZeroPulse/memory/zp-pipeline-runbook.md
olusturma: 2026-10-29
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
**Material folder:** no fixed names. `new_episode.py` takes the BIGGEST `*.txt` as script and BIGGEST `*.wav` as voice ref (recursive); thumbnail is not read. Script formats: `TOPIC:` + `NN. TITLE` headings, or EP02 markdown table `| **NN. TITLE** | narration | visual |`, else Flash extracts. `NNN wpm` in text overrides 165. Flash is always needed (topic + CTA line).

**Steps**
1. `python pipeline/new_episode.py <material> epNN [--minutes 2]` (2-min preview first, user approves)
2. Check `episodes/epNN/episode.json`: `voice.engine` defaults to `sopro` (verified 11-06 in tts_sopro.py/cta.py; device is decided by the Sopro server :7862, which must run on CPU); pronunciations, cta.
3. `python pipeline/run_episode.py episodes/epNN` — stages: voice|plan_v4|cut_plan → words_ts → align|asr_check → plan_v5 → gen2|cut_render|cta → build8 → finalize → qa. Resume is mtime-based; `--until X` stops after X's whole stage. Logs in `logs/<step>.log`.
4. Several episodes: `LANES=2 GLABS=3 python pipeline/batch.py episodes/epA episodes/epB` (env only; GLABS = total G-Labs threads, split per lane).

**Before delivery (all 0 / read):** `qa.md`, `assets2/missing.json` (icon stand-ins, gen2 exits 0 anyway!), `python pipeline/blankcheck.py episodes/epNN/out/final.mp4`, `python pipeline/gridcheck.py <clips>`.

**Gotchas in code**
- batch.py ignores exit codes: gen2 exit 3 only marks that episode failed, next episodes keep hitting the dead G-Labs. Watch `episodes/batch.log`.
- Manual gen2/build8 need `PLAN=plan_v5.json` (default plan2.json).
- finalize deletes the ~1.8 GB master unless `KEEP_MASTER=1`.
- build8 runs NPARTS=6 processes, libx264 lossless (no NVENC) — RAM heavy, run alone.
- Whisper silently falls back to CPU (~8 min) if GPU is full.
- Start G-Labs (127.0.0.1:8765) before gen2. Flash gateway is on Tailscale (100.x).

**Old chat files** (`eski_sohbet_dosyalari/`): not in library: `P03_ayna.png` pose, mascot refs `maskot_A/B/on.png`, scoring JSONs/comparison jpgs, all EP01/test mp4s (archive only).
