# Case File builder — spec (2026-11-05)

Goal: turn one finished documentary-pipeline film into a ~10 min WRATH OF EARTH "Case File" edit, the style of
`referans/EP01_WRATH_OF_EARTH_V2.mp4` (notes: `referans/EP01_V2_EDIT_NOTLARI.md` — READ IT, it is the style bible)
and of our 1-min sample (`ornek/`, tools in `ornek/tools/`, output `Channells/ENGINEERED/WOE_SAMPLE_ENDERLIN_CASEFILE_JEFF.mp4`).
The original V2 scripts (v2_assets.py / v2_build.py) are on another machine; we rebuild the idea here, generic for any film.

## Input (per film)
`C:\Users\meteh\CodexOutputs\<FILM>\` after stage 4: `material_plan.json`, shot clips (paths as in
`documentary_materials/delivery.py::_edl`), `master_voiceover.wav` (in the project folder), `narration_plan.json`,
sentence timings (`delivery.py::_sentences`). Script folder: `Downloads\Compressed\drive-download-20261105T125326Z-1-001\<FILM>\`
(script md + fact sheet if any). Import pipeline helpers read-only; never edit `C:\Users\meteh\.gemini\scripts`.

## Steps (one CLI: `python casefile/cf.py <FILM> [--plan|--assets|--build|--preview|--only a-b]`, each step cached)
1. **Editorial plan** (`work/<FILM>/cf_plan.json`), drafted by GPT (`gpt-6-sol`, VDS :8765 — see how the pipeline calls it;
   fallback `ag/gemini-3.8-flash-low` via 9router) from the EDL rows + narration + script, then validated in code:
   - sections (hook, 4–6 parts, epilogue) with title + optional struck-through tease line; mode per section
     (FULL / COLLAGE / PRINT / MONITOR; hook+epilogue FULL). Overrides: 3D → MONITOR, PHOTO → PRINT, ANIM full-frame.
   - replace weak clips (MOTION/CARD one-word cards, TV-graphic/news-logo clips) with own graphics:
     document card + red pen ring, big number (Bodoni) + label, date/time typewriter, map/path line, scale bar, quote card.
     **Facts only from the narration/script text of that clip's window**; every representative document gets
     "ILLUSTRATIVE LAYOUT", diagrams/radar "SIMPLIFIED ILLUSTRATION". Never invent numbers, names, quotes.
   - location/time lower-thirds (~20–25 per film) from narration (place + time when said).
   - Flow replacements: the hook clips (≈10) + any clip with on-screen text/logo/watermark (use the pipeline's own
     review data in shot result.json if it flags text/watermark; else skip). Prompt = locked STYLE block (notes §4) + one ACTION line.
   - memorial line at the end if the film has deaths (wording from the script, calm, no SFX), end card (logo, "Every fact in this film is sourced in the description").
2. **Assets**: graphics rendered as PNG/short MP4 (reuse the HyperFrames/HTML look of `ornek/tools/build_hf.py`: fonts in
   `ornek/woe_sample/assets/fonts`, colours #0B0F10/#E8E2D3/#C02622, topo bg from `make_topo.py`).
   Flow clips via `ornek/tools/gen_flow.py` (G-Labs 127.0.0.1:8765, max 3 parallel, Flash gate on stills), cropped as `prep_flow.sh`.
3. **Build**: ffmpeg segments per EDL row in its mode (FULL letterbox + slow pan; PRINT tilted print on drifting topo with paper edge
   + shadow, 0.5 s slide-in; COLLAGE torn-edge print on aged newspaper + red tape; MONITOR glowing monitor on perspective grid),
   section cards, 8-frame dip-to-black between sections, light temporal grain (noise=alls=4), WRATH OF EARTH watermark top-right
   (not on end card), lower-thirds slide in 0.45 s. Timeline must stay locked to the voice (each segment = its EDL window).
   Audio: voice -16 LUFS; music bed = synthesized drone with sidechain (see `ornek/tools/mix.py`) varying per section;
   SFX trimmed per notes §6 (pen ring 0.75 s, pen line 0.45 s, paper 0.8 s, typing = typing time, sub hit 2.2 s on number cards,
   boom 2.8 s on section cards), library `C:\Users\meteh\.claude\skills\media-use\audio\assets\sfx`; final limiter 0.85.
   Output 1920x1080 25 fps H.264 CRF 19, AAC 320k → `C:\Users\meteh\OneDrive\Desktop\Channells\ENGINEERED\<FILM>\<FILM>_WRATH_OF_EARTH_CASEFILE.mp4`.
4. **QA** (`work/<FILM>/qa/`): contact grids every ~10 s, check text overlap / safe area / leftover watermarks; per-section LUFS;
   duration == voice duration (+ end card); report `CASEFILE_QA.md`.

## Constraints
- 16 GB RAM machine, other films may be producing: before heavy render check free RAM ≥ 2.5 GB, wait otherwise; segment renders
  ≤ 2 parallel ffmpeg; use libx264 (NVENC is the pipeline's).
- No license-watermarked footage left visible. No generated real-person faces. Production text English.
- Deterministic and cached: rerunning a step reuses finished segments/assets (hash of inputs).
- Keep code compact (target ≤ ~900 lines total, several files ok), generic — nothing hard-coded to one film.
