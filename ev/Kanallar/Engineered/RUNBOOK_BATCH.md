# ENGINEERED batch runbook (commander session)

Read this before touching a batch. Links, not copies: open the file for detail. Error classes follow
`documentary_materials\docs\ARCHITECTURE_40_PER_DAY.md` section 4.4. Paths: ENG = `C:\Users\meteh\Kanallar\Engineered`,
OUT = `C:\Users\meteh\Belgesel_Teslim`, RUN = `C:\Users\meteh\CodexOutputs\<film>`.

## 1. Start of batch
1. `python C:\Users\meteh\Kanallar\preflight.py` (about 13 s; `--json` for machine output; exit 1 = a critical FAIL, do not start).
   Warnings (free RAM) mean fewer films at once, not a stop.
2. Bridge :8099 must listen (preflight prints it). If not: in `C:\Users\meteh\.gemini\scripts` run `python documentary_native_bridge.py` hidden; log `documentary_native_bridge.log`.
3. Queue a folder of film folders: `python ENG\tools\queue_films.py "<parent>" [max_parallel=3]`, background. Log: `OUT\batch.log`, per film `OUT\queue\<film>.log`.
4. One film by hand, admitted by RAM and film count: `bash ENG\tools\run_when_free2.sh "<film folder>" <start stage>` (4 films, 4 GB free RAM; do not edit the .sh while it runs).
   Direct form: `python ENG\tools\drive.py "<folder>" <start> 4 [profile]`.
5. Watcher: `python ENG\tools\supervisor.py --prime`, then `python ENG\tools\supervisor.py` in the background. It runs forever and requeues resumable failures itself (autoresume.py: exit 2/3/4/10 from the failed stage, exit 11 after a wait, max 3 per film and stage, then an `autoresume_capped` incident; `--no-resume` turns it off). Lines `autoresume:` in batch.log.
   It calls GPT and Flash on an incident and writes `OUT\incidents\<time>_<kind>.md`: read that file first, it already holds a diagnosis.
6. Wait for a film without wake-ups: `python ENG\tools\wait_film.py <film|all> --until any` (one line out, documented exit codes, `--help`).

## 2. How to read state (cheapest first)
1. `OUT\batch.log` tail: one line per start, stop, retry, exit. Lines "exit 0" before 14:31 on 2026-10-30 are not trustworthy.
2. `OUT\queue\<film>.log`: per stage `[stage N] http= status=` and the error JSON. Read the last 15 lines only.
3. `RUN\03_materials\events.jsonl` (stage 3 and later; mtime = last sign of life) and `RUN\voice_progress.json` (stages 1-2). Count stages, do not read the whole file.
4. `RUN\03_materials\REPORT.md` (why stage 3 stopped) and `shots\<id>\result.json` (`status`, `review.data`).
5. `RUN\voice_audit.json` for a stage-1 FAIL (the HTTP body carries `error_type: null`).
6. `status.json` does not exist yet (Q3/Q7); use it only if present.
7. Is a film alive: `RUN\run.lock` plus a drive.py process for that folder name. A lock without a process is a leftover.
Stage OK values: 1 SUCCESS/PASS, 2 PASS, 3 MATERIALS_READY, 4 PASS or PASS_WITH_NOTES. drive.py exits with the failing stage number.

## 3. One action per error class
| Class | Recognise by | Do this | Tries |
|---|---|---|---|
| transient_llm | ReadTimeout on 9router, Gemini 503/429, GPT timeout, stage-1 PASS_DEGRADED/UNVERIFIED | Stage 1: audit-only rerun (drive.py does it). Other stages: rerun the same stage after 2, 5, 15 min | 3 |
| transport | ConnectionRefused/Reset, URLError, non-JSON body from :8099 | Wait until the bridge answers, then rerun the same stage (`run_when_free2.sh "<folder>" <stage>`) | 3 |
| duplicate_job | "already has an active production job" | Do not retry; attach with `wait_film.py <film>` | 0 |
| voice_text | stage-1 FAIL, `voice_audit.json` text_completeness FAIL, voice match PASS | `python ENG\tools\redo_voice.py "<input folder>"` (repairs flagged chunks only), then stage 2 | 1, then park |
| allocation_short | "No feasible narrative/category allocation", `ALLOCATION_SHORT:<cat>` | Do NOT rerun unchanged and do not change ratios. Find the short category in the `plan_loop`/expansion events, top it up (more sources for that category), rerun stage 3 once | 1, then park |
| search_down | SearXNG :8888 probe fails (preflight FAIL) | Start Docker Desktop, `docker start searxng`; film waits, no try used | - |
| glabs_down | "Max Retries Exceeded", G-Labs :8765 unreachable | Restart G-Labs, keep at most 3 parallel jobs; ANIM shots fall back, the film continues | - |
| route_dead | same review verdict twice on one route (e.g. 3D `visual_fit` FAIL, `unreadable_3d_diagram`, shot in `rejected.json` three times) | Stop re-rolling that route. Move the shot to another route (ANIM, archive photo or footage) and rerun stage 3; a manual accept goes in `delivery_waivers.json` only for a real false alarm | per shot |
| code_bug | KeyError, TypeError, WinError 32, "has an empty name" in the log | Park the film; read the traceback once; fix in testbench first (never in prod mid-batch) | 0 |
| resource | low RAM, paging, C: low, Pocket/9router down | Wait; lower parallel films; no try used | - |
| unknown | anything else | Park; open the incident file, then wake the user if it does not name a cause | 0 |
The queue retries stage 3/4 stops by itself, 3 times 20 s apart: that is a burst of identical failures, not progress. After "retry 3" the film is FAILED; do not requeue it unchanged.

## 4. Never done by hand
- `documentary_materials\yt_gate.py` budget and pacing; start no bridge or script that skips it.
- Slot, NVENC and RAM limits (`C:\Users\meteh\.gemini\scripts\system_speed_profile.json`); never raise them to speed a film.
- QA thresholds, judge prompts and models, tests: no loosening without a frame or measurement and the user's yes.
- Never `Stop-Process` a drive.py or bridge you did not start; never edit a running `.sh`; never run Sopro on the GPU.
- Do not send test traffic to :8099 and do not use the bench lock `C:\Users\meteh\testbench\.bench_lock` that others hold.

## 5. When to wake the user
- delivered films (ZIP in `Channells\ENGINEERED`) and film FAILED after the retries above;
- class unknown or code_bug, or a class marked "then park" already used its try;
- C: below 30 GB, or a judge that looks wrong (give the frame path);
- a decision outside this file: new sources to buy, loosening anything in section 4, deleting data.
Everything else (transient, transport, resource, glabs_down, search_down) you handle and report in one line.
