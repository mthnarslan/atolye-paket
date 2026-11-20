# 40 films per day: target architecture for the documentary line

- **Date:** 2026-10-30.
- **Author:** the architect agent of workflow wf_273ca692, in a read-only pass. No code was changed and nothing was committed.
- **Work items:** `docs\WORKPLAN_40_PER_DAY.md`. The IDs Q*, A*, B*, C* and T* used below refer to it.
- **Number labels:**
  - Plain numbers were **measured** on 2026-10-30, from logs, the process table and run folders.
  - Numbers marked *estimate* were derived; the derivation is shown next to them.
  - Anything else not measured is listed in §11 (Unverified).

**Path shorthands**

| Shorthand | Path |
|---|---|
| DM | `C:\Users\meteh\.gemini\scripts\documentary_materials` (production repo, git main) |
| SCR | `C:\Users\meteh\.gemini\scripts` |
| ENG | `C:\Users\meteh\Kanallar\Engineered` |
| TB | `C:\Users\meteh\testbench` |
| VL | `C:\Users\meteh\codex-repo-tests\voice-lab` |

---

## 1. Verdict and KPIs

### Verdict

1. **This PC cannot make 40 films of about 15 minutes per 24 h at today's cost per shot.**
   - Stage 3 alone needs 29.3 machine-hours per day. Only 19.4 hours are usable (151%, §6.2).
   - 40/day becomes possible when two things hold:
     - Machine-seconds per accepted shot fall from 13.9 (*estimate*) to 9.2 or less, a 34% cut.
     - Three outside supplies are secured: G-Labs assets, LLM calls after GPT ends, and 40 scripts per day plus publishing. For G-Labs, 40/day needs 143–263% of today's ~1,400 assets per night.

2. **Today's output is limited by failures, not by capacity.**
   - The 2026-10-30 batch started 9 films and delivered 1 (EP04).
   - 27% of in-flight film-minutes were idle, there were about 14 manual runs, and 6 of 9 films failed stage 1 first time.
   - On paper the PC already has room for about 27 films/day (220 accepted shots/h × 24 h ÷ 190 shots per film).
   - Reliability work therefore comes first, and it is cheap.

3. **The plan has five phases, each with a measured gate.**

   | Phase | Goal |
   |---|---|
   | 0 | Quick safe wins |
   | A | A reliable 10/day with zero manual runs |
   | B | 20/day on the same hardware, by cutting waste |
   | C | 30–40/day |
   | T | Claude token economy (runs in parallel with the others) |

   Gate C1 picks the purchase from evidence: 32 GB RAM if paging binds, or a rented Hetzner AX42 HyperFrames worker (€99/month + €49 setup) if CPU binds.

4. **Backbone: design D3 (quality and risk first), with grafts.**
   - From D1: the capacity metric, CPU tokens, tail admission, one ffmpeg per source, and a HyperFrames preset A/B.
   - From D2: the SearXNG fix, the feasibility gate, the token ledger, the remote-call contract, and prescan as sources arrive.
   - From the judge: paging, in-flight disk, the governor baseline, error plumbing, and EP05.

5. **What does not change:**
   - Judges, QA thresholds and prompts, tests, `yt_gate`, and NVENC and slot limits. The slot limits are in `SCR\system_speed_profile.json`: hyperframes 5, nvenc 5, cpu 4, voice 1, flash 15, codex 12. None is relaxed without evidence and user approval.
   - No logo or watermark removal, English production, and real footage first.

### KPIs

| KPI | Today | Phase A exit | Phase B exit | Phase C exit |
|---|---|---|---|---|
| Films delivered per 24 h | 1 of 9 started | 10 | 20 | 40 for 7 days |
| Manual runs per day | about 14 | 0 for 3 days | 0 | 0 |
| Idle share of in-flight film-minutes | 27% (379 of 1,416) | <15% | <10% | <10% |
| Accepted shots per wall-hour (24-h mean) | ~220 capacity (*estimate*) | measured (Q1) | ≥158 | ≥317 |
| Machine-seconds per accepted shot (MSPS) | 13.9 (*estimate*) | measured (Q1) | ≤13.9 | ≤9.2 |
| Voice first-audit pass | 3 of 9 films | ≥60% | ≥80% | ≥80% |
| Pocket speed under load | 0.19x realtime (2.83x alone) | ≥1.0x | ≥1.8x | ≥1.8x |
| Allocation crashes | 3 films (EP05, EP07, EP08) | 0 | 0 | 0 |
| Delivered shot-type mix | EP04 off by up to 9.2 pts per type | measured per film | within ±5 pts | within ±5 pts |
| PARTIAL-accepted shots per film | 81 (EP04) | tracked | not above baseline | not above baseline |
| C: bytes left per delivered film | 5.4 GB | ≤0.3 GB | ≤0.3 GB | ≤0.3 GB |
| Judge or threshold relaxations without approval | 0 | 0 | 0 | 0 |
| Claude wake-ups | one per incident; notification wake-ups 4.99M wM/day (14.5%) | unknown classes only | same | same |

---

## 2. Current state (2026-10-30)

### 2.1 Flow today

```
script folder (ad hoc, e.g. Downloads\Compressed\drive-download-...)
  ENG\tools: queue_films.py (in-memory queue, MAX 3) + run_when_free.sh x4 (60-s pollers) + manual runs
    drive.py: one blocking POST per stage to the bridge (timeout 24 h)
bridge SCR\documentary_native_bridge.py :8099
  - binds 0.0.0.0; one ThreadingHTTPServer process
  - Dify also calls it at host.docker.internal:8099 (update_dify_4stages.py:50/94/138)
  - reloads documentary_materials.* and adaptive_governor on every stage POST
  - reloads its own source when the file changes
  stage 1 voice     Pocket TTS :7863 (CPU, one lock, per sentence) -> faster-whisper base.en
                    -> Gemini audio review -> repair loop of up to 3 rounds
  stage 2 timeline  Whisper alignment -> Flash scene plan -> GPT reviewer
  stage 3 materials catalog -> MILP plan (DM\planning.py make_plan :1092)
                    -> 15 shot workers (DM\runner.py _work_shot :3618) -> grid_prefilter
                    -> render_with_qc (NVENC) -> Flash and GPT review
  stage 4 final     DM\render_stage.py: concat -> null decode
                    -> DM\delivery.py ZIP_STORED -> OneDrive Desktop\Channells\ENGINEERED
supervisor.py: wakes Claude per incident, then exits
preflight.py:  runs once before a batch
External:
  - Flash: 9router on VDS 100.104.78.117:20128, via the DERP relay "nue"
  - GPT gateway: VDS :8765
  - own Gemini keys (free tier)
  - G-Labs API 127.0.0.1:8765
  - SearXNG (Docker) :8888
  - YouTube through yt_gate with Firefox cookies
  - BBC library
```

### 2.2 Throughput and stage times

| Measure | Value |
|---|---|
| Batch of 2026-10-30 | 9 films started at 11:05; 1 delivered (EP04, 14:04:46); 1 film per 3.55 h of batch time |
| EP04 end to end | 176 min of wall time, with about 5 films in flight |
| In-flight film-minutes | 1,416, of which 1,037 were active and 379 (27%) idle |
| Manual (re)starts | about 14; 12 of the 56 batch.log lines are manual starts |
| Stage 1 | 1,135–1,341 s when it passes; 1,804–5,706 s when it fails |
| Stage 2 | 38–174 s |
| Stage 3, EP04 | four calls: 7,347 + 940 + 406 + 219 s |
| Stage 3 span, EP02–EP04 | 152–173 min (detail below) |
| Stage 4 | 391 s |
| Shots per film | 178–211; this document uses 190 accepted shots per film |

The 152–173 min stage-3 span (EP02–EP04) breaks down as:
- planning: about 18 min (18.9 for EP04; 17.8 for EP02 and EP03);
- first pass: 77–100 min;
- tail: 56–60 min, about 35% of the span, running at 1–5 workers.

### 2.3 Where stage-3 time and money go

**Share of timed worker seconds, EP02–EP04**

| Step | Share |
|---|---|
| render_with_qc | 48–52% |
| anim_make | 13–16% |
| grid_prefilter | 11–14% |
| media_gate_wait | 8–9% |
| precheck | 6–9% |

- About 25–30% of worker time is not timed at all.
- Total step-hours per film: 21.1 (EP02), 26.3 (EP03) and 20.4 (EP04).

**render_with_qc, seconds**

| Shot type | Values |
|---|---|
| MOTION | median/mean 126/164 (EP02), 132/220 (EP03), 211/320 (EP04) |
| CARD | median/mean 77/91 (EP03), 124/139 (EP04) |
| VIDEO | median 41–48 |
| 3D | median 35–74 |
| ANIM | 6–8 |

**Waste**

| Kind of waste | EP02 | EP03 | EP04 |
|---|---|---|---|
| Retries, share of step seconds | 31.5% | 37.8% | 33.4% |
| Render and anim seconds spent on shots that did not pass | 29.8% | 46.4% | 37.7% |
| 3D shots that did not pass | 82 of 138 | 156 of 189 | 77 of 109 |

Duplicate prescans cost about 10,300 s. Commit e936d45 fixed this, so the 2026-10-30 baseline overstates today's cost.

**Shot-type mix (%)**

| | VIDEO | PHOTO | 3D | CARD | MOTION | ANIM |
|---|---|---|---|---|---|---|
| Target | 40 | 10 | 10 | 15 | 10 | 15 |
| EP04 delivered | 49.2 | 2.0 | 17.0 | 6.8 | 18.6 | 6.6 |

- EP04 accepted 81 shots as PARTIAL.
- EP02 used 68 MOTION shots and 50 3D shots.
- Failed VIDEO allocations: 98 of 193 (EP02), 75 of 211 (EP03), 32 of 180 (EP04).

**Tokens per film (stage 3)**
- Input: 7.0–11.9M. Output: 0.34–0.62M.
- Input shares: per-shot Flash review 24–26%, Pinpoint 9–19%, GPT review 12%, precheck 6–7%, grid 4–7%.
- If these lanes were paid, exposure would be $2.9–11.2 per film.

### 2.4 Failure profile of the 2026-10-30 batch

**Stage 1**
- 6 of 9 films failed first time:
  - EP02: 9router ReadTimeout on 5 of 6 audit segments;
  - EP08: Gemini 503;
  - also EP06, EP07, EP09 and EP10.
- All 12 failed audits were text_completeness FAIL while voice match passed.
- Repairs: 6 of 9 films needed them, totalling 10 rounds and 16 rewrites. 15 of 702 chunks (2.1%) were garbled.
- One repair round takes 5–15 min:
  - resynthesis 17–100 s;
  - master rebuild 39–204 s;
  - ASR 30–130 s;
  - audit 100–525 s.

**Stage 3**
- From about 11:26 to 14:45 the SearXNG image engines were dead, but the health probe (`/search?q=test`) still passed. With 0 archive photos, EP07 and EP08 failed with "No feasible narrative/category allocation".
- EP05 failed the same way. Its cause is unknown: it had 41 photos.
- EP06 crashed because `docker start searxng` hit its 60-s timeout and the timeout was not caught.
- EP02 GENERATE_3D shots 61, 91 and 125 failed visual_fit on every attempt, with identical review text.
- One crash in `render.py:240`: "WindowsPath('.') has an empty name".

**Orchestration**
- EP05 waited 2 h 03 min to be admitted, then used retries 1–3 within 40 s.
- `run_when_free.sh` uses `-le 4`, so it admits a fifth film. EP07 and EP09 started in the same second.
- The bridge rejected a duplicate EP02 launch, but the log recorded it as "exit 3".
- "exit 0" lines in batch.log before 14:31 cannot be trusted.
- The supervisor misses films started from stage 2 or 4.

**Services**
- G-Labs went down at 11:33:53 ("Max Retries Exceeded").
- 9router timed out, and Gemini returned 503s.

### 2.5 Machine

**RAM.** The machine is RAM-bound, so part of what looks like CPU contention is paging.
- 1,664 of 16,163 MB were free with about 5 films in flight.
- Pagefile: 4,459 MB in use; peak 14,433 MB.
- Bridge: 6,394 MB private, 1,091 MB resident.
- Pocket (PID 16020, Normal priority): 3,033 MB private but a 2 MB working set, so it was paged out. Each drive.py had a 0–2 MB working set.

**CPU**
- About 64% of CPU time goes to short-lived child processes: ffmpeg and ffprobe, Chrome for HyperFrames, and the 3D renderer.
- On the testbench the split was ffmpeg/ffprobe 18–45%, Chrome and other 12–41%, and the bridge 8–12%.

**GPU.** An RTX 3050 Ti 4 GB. Mean use is 11% and memory peaks at 2.9 GB, so the GPU is not a bottleneck.

**Disk C:**
- Each film takes 5.35–5.4 GB (a 3.7 GB folder plus a 1.78 GB ZIP).
- EP03, still in flight, is 7.64 GB; the nine film folders total 30.4 GB.
- yt_cache is 14.7 GB.
- 135.9 GB are free.

### 2.6 Voice

- 858 s of audio per film (2,000–2,650 words).
- Pocket's speed:
  - alone: 2.83x realtime, about 306 s of synthesis per film;
  - aggregate on 2026-10-30: 0.48x (15,998 s of synthesis for 7,720 s of audio);
  - under contention: 0.19x, or 71–80 min per film.
- Speaker similarity (ECAPA): baseline 0.748; Sopro 0.838.
- WER: 2.8%.

### 2.7 LLM lanes

**Calls per film**

| Film | Flash | GPT (codex) | flash_review | gdirect |
|---|---|---|---|---|
| EP02 | 1,026 | 357 | 138 | 12 |
| EP03 | 1,334 | 543 | 149 | 22 |
| EP04 | 884 | 409 | 87 | 17 |

**Behaviour**
- Median latency is 8.0 s for Flash and 13.5 s for GPT.
- 4% of Flash calls fail.
- Flash peaked at 23 concurrent calls against a cap of 15, because the governor is reset on every module reload (ops gap 1).
- 9router is reached through a DERP relay, not a direct path.
- The own Gemini keys served about 46 successful calls today: 23 of 46 key×model pairs were marked spent.
- flash-low as a GPT replacement agreed 78% of the time, with 20% false PASS.

### 2.8 Other services

| Service | Today |
|---|---|
| G-Labs | About 1,400 assets per night, shared with SkullStudio. Documentaries use 50–92 assets per film; 8–27 ANIM shots per film failed |
| yt_gate | 41.7 calls/min (60k/day) at concurrency 3 |
| SearXNG fact-check | 28–112 searches per film, 161–337 s, run one after another |

### 2.9 Claude orchestration

- Steady state is 34.5M wM/day over 2,058 calls. The commander session takes 73%.
- Notification wake-ups cost 4.99M wM/day.
- A main call costs about 19.6k wM regardless of result size, so cost follows the number of calls.
- Sessions compacted 13 times, at 166–169k.
- Each of the roughly 14 manual runs a day pulls Claude in.

### 2.10 What the reference numbers mean

- The 18.5-minute best time was TOPIC_2, a 3:52 wildlife film made on 2026-10-24, not Mayfield. That is about 4.8 wall-minutes per film-minute, solo.
- The ≤15-minute target was set for 4–5-minute films. For a 15-minute film, planning alone takes about 18 minutes.
- The target needs re-basing; this is decision D1 in §10.

---

## 3. Principles

1. **Measure, then change one stage at a time.** Every change goes testbench → DIFF_MINI (at least 2 runs per side) → one canary film → production.
2. **Judges are fixed points.** Throughput comes from less waste (failed renders, dead routes, idle time, duplicate decoding, paging), never from looser review.
3. **One writer for production state.** A single ledger daemon writes it; everyone else reads it.
4. **Every remote call has a contract** (§4.2): a timeout, a local fallback, a switch read on every call, and a shadow test before real use.
5. **Every failure gets a class and exactly one next action.** Unknown failures go to Claude; nothing is retried blindly.
6. **Capacity is bought only after a gate names the binding resource**: paging means RAM, CPU means the AX42. The GPU is not binding.
7. **No capacity is built on free tiers.** Free Gemini keys are burst and backup only.
8. **Variety is planned and tracked per channel**: source ledger, template ledger, identity packs. It does not come from random effects.
9. **Production never stops.**
   - Changes ship as hot-reloadable modules or new files.
   - Shared services restart only in drain windows.
   - Shell scripts that are running are never edited.
10. **Claude handles exceptions; it does not schedule.**

---

## 4. Target architecture

### 4.1 Service split

```
PC (16 GB RAM, RTX 3050 Ti)
  intake (C10) -> ledger daemon: sqlite WAL, single writer; classifier; admission
                    |- voice queue (B9): stages 1-2 for the next 2-4 films
                    '- materials queue: stage 3-4, admission rules (section 4.5)
  bridge :8099 (one process; state survives reload A1; reload errors refuse the stage Q7; async jobs C14)
     stage 1 -> Pocket :7863 (FIFO lock, AboveNormal, ASR pre-gate B2, repair endpoint B13)
     stage 2 -> Flash / GPT through the remote-call contract
     stage 3 -> governor: CPU tokens B3, slot limits unchanged
                sources:  yt_gate, BBC, SearXNG (health on image results Q6), direct photo APIs + credits (A2)
                renders:  ffmpeg/NVENC (one ffmpeg per source B4), HyperFrames (B5), 3D (still pre-check B6),
                          G-Labs ANIM (budget B14, breaker A5)
                plan:     feasibility gate before the MILP (A2), fallback ladder (A5), prescan on arrival (B8)
     stage 4 -> render_stage (per-film temp B11) -> delivery staging + sha256 -> retention (A3)
  sampler (Q1) . supervisor (Q5) . deep preflight (A6) . service wrapper (A7)
VDS 100.104.78.117: 9router Flash :20128, GPT gateway :8765 (contract; direct path C13; inventory C12)
AX42 (only if gate C1 says CPU): HyperFrames MOTION/CARD worker (C2), local fallback
External: G-Labs, YouTube, own Gemini keys (backup), photo APIs, OneDrive or archive target
```

| Component | Role | Host | State | Items |
|---|---|---|---|---|
| Ledger, admission, classifier | Single writer for film state; stage calls; backoff; drain mode; status.json; daily report | PC | `ENG\ledger\films.db` (sqlite WAL) | A4, B7, B9, C8, C14 |
| Bridge :8099 | Runs stages; hot-reloads modules | PC | run folders; run_registry and scan_cache survive reload | Q7, A1, B13, C14 |
| Governor | Slot limits from `system_speed_profile.json`; CPU tokens; wait metrics | PC (inside bridge) | in process, kept across reloads | A1, A9, B3 |
| Voice lane | Pocket FIFO, voice-ahead, ASR pre-gate, repair endpoint | PC | voice lock kept across reloads | B1, B2, B9, B13 |
| Stage-3 engine | Plan, select, render, review | PC | run folders, scan_cache | A2, A5, A10, B4, B5, B6, B8 |
| Source supply | SearXNG, photo APIs, yt_gate (pacing unchanged), BBC | PC | yt_cache (LRU cap), source ledger | Q6, A2, A3, C5 |
| LLM lanes | Flash (9router), GPT gateway (ending), own keys (backup), paid lane (only if needed) | VDS and external | gemini_usage.json | Q12, A8, C3, C4, C13 |
| G-Labs | ANIM assets | local API to an external service | shared daily budget file | B14, C7 |
| HyperFrames worker | MOTION/CARD renders | AX42 (conditional) | none; the switch file decides | C2 |
| Storage lifecycle | Staging, sha256, per-channel roots, retention | PC, then archive | manifest per film | A3, B11 |
| Observability | Sampler, events, status.json, daily report, token ledger | PC | `TB\prod_sampler`, ledger tables | Q1, A9, A10, T14 |
| Supervisor | Long-lived; notifies; wakes Claude for unknown classes only | PC | incidents folder | Q5, T1 |
| Preflight | Deep checks, every 10 min, feeds admission | PC | none | A6 |

### 4.2 Remote-call contract (VDS, AX42, any rented host)

1. **Hard timeout per call.** On a timeout or a 5xx, the work runs locally or on the next lane. A remote failure never fails a film.
2. **A switch read on every call**, for example `%LOCALAPPDATA%\documentary_materials\remote.json` with `{"hyperframes": {"enabled": false, "share": 0.0}}`. Turning a lane off needs no restart.
3. **Shadow first.** The remote result is computed and compared but not used:
   - renders must reach SSIM ≥0.999;
   - LLM calls must reach decision agreement.
   Then roll out to 10% and later 100%.
4. **Direct network path before per-shot traffic.** A Tailscale direct connection, not the DERP relay. RTT and throughput are logged per day.
5. **Secrets.** None in URLs. Keys come from the existing stores (`vds_secret_store.py`, `gemini_keys.py`) and are never printed or logged.
6. **Accounting.** Each call writes lane, host, latency, bytes and outcome to the film's events, so the daily report shows remote share and fallbacks.

### 4.3 Ledger (stdlib `sqlite3`, WAL mode, one writer)

| Table | Columns |
|---|---|
| `films` | `film_id` PK, `folder`, `channel`, `profile`, `stage`, `state`, `attempt`, `next_try_at`, `last_class`, `last_error`, `pid`, `started_at`, `updated_at` |
| `runs` | `run_id`, `film_id`, `stage`, `started_at`, `ended_at`, `exit_code`, `http_status`, `status`, `error_type`, `error_class`, `wall_s` |
| `events` | `ts`, `film_id`, `kind`, `detail_json`; append-only, mirrored to `events.jsonl` |
| `resources` | `ts`, `free_ram_mb`, `page_reads_s`, `cpu_pct`, `c_free_gb`, `services_json`; filled by the Q1 sampler |
| `tokens` | `ts`, `film_id`, `lane`, `model`, `calls`, `input_tokens`, `output_tokens`; filled from A9 events |

`state` takes one of: queued, voice, waiting_stage3, running, waiting_resource, backoff, parked_needs_user, done, failed.

**Process rules**
- The daemon is the only writer.
- Claude, the supervisor and reports read `status.json` and the database.
- **Drain mode:** no new admissions; in-flight films finish.
- **Shadow mode:** for 48 h the daemon reads queue logs and the process table and records the decisions it would have made, beside `queue_films.py`.
- **Cutover:** at a batch boundary. The old scripts are kept until 3 clean days have passed; retiring them is a user decision.

### 4.4 Error classes and actions

| Class | Signals | Action | Attempts |
|---|---|---|---|
| transient_llm | 9router ReadTimeout; Gemini 503 or 429; GPT gateway timeout; stage-1 verdict PASS_DEGRADED or UNVERIFIED | Stage 1: audit-only rerun (today's `drive.py` reaudit). Other stages: retry the same stage after 2, 5 and 15 min | 3 |
| transport | Stage client exit 10 (URLError, connection reset, non-JSON body) | Wait for bridge `/health`, then retry the same stage | 3 |
| duplicate_job | "already has an active production job" (exit 11) | No retry; attach to the running job | 0 |
| voice_text | Stage-1 FAIL; `voice_audit.json` shows text_completeness FAIL while voice match passes | Targeted repair through the repair endpoint (B13), then a new audit | 1, then park |
| allocation_short | `ALLOCATION_SHORT:<category>` (A2), or "No feasible narrative/category allocation" | Top up that category (A2 d/e), then rerun stage 3 from planning | 1, then park |
| search_down | SearXNG image probe fails or `docker start` times out (Q6) | Wait for the resource and repair it; no attempt is used | – |
| glabs_down | "Max Retries Exceeded"; G-Labs breaker open | ANIM shots move down the ladder (A5); the film continues | – |
| route_dead | Same review signature twice on one route (A5) | Switch route, inside stage 3 | per shot |
| code_bug | Python exception types (KeyError, TypeError), WinError 32, "has an empty name" | Park; wake Claude once with the traceback | 0 |
| resource | Free RAM or paging past threshold; C: below reserve; Pocket or 9router down | Wait; no attempt is used | – |
| unknown | Anything else | Park; wake Claude | 0 |

Today's plumbing hides these classes, so the classifier must work around three facts:
- A stage-1 FAIL carries `error_type: null`. The classifier reads `voice_audit.json` instead.
- An allocation failure returns HTTP 500, the same as a crash. The classifier reads the message text; Q3 and Q7 make codes and bodies honest.
- batch.log "exit 0" lines before 14:31 are untrustworthy. Evaluation uses queue logs and bridge bodies instead.

### 4.5 Admission rules (checked every 20 s, at least 90 s after the last admission)

The materials queue (stages 3–4) admits the next film only if all of the following hold:

1. **Film count.** In-flight stage-3/4 films < MAX.
   - MAX is 3 today; 4–5 only after C8 and user approval.
   - With B7 approved, a film in its stage-3 tail counts as 0.5. A tail film has 5 or fewer active workers for at least 5 min.
2. **Memory.** Free RAM ≥2.5 GB, and the 60-s mean of `\Memory\Page Reads/sec` is below the threshold derived from Q1.
3. **Disk.** C: free ≥ 20 GB + 6 GB × films in flight.
4. **Services.** The bridge `/health` passes, and the deep preflight passes for Pocket, 9router, SearXNG image results and the GPT gateway. G-Labs must also pass if ANIM's share is above 0.
5. **Inputs ready.** Stages 1–2 have passed (the voice-ahead queue, B9).

**Order:** first-in first-out by script arrival, round-robin across channels.

**The voice queue** runs stages 1–2 for the next 2–4 films. Pocket's FIFO lock serializes the work, and the queue needs no stage-3 slot.

### 4.6 Voice lane

- **One Pocket server, one FIFO lock across films.** The lock survives module reload; the pattern is the VOICE_LOCK at `ENG\tools\batch_films.py:66-96` combined with `globals().get`.
- **Pocket process settings:**
  - AboveNormal priority, never Realtime;
  - `RECYCLE_MB` (`pocket_serve.py:64`, 3500 today) set from the Q14 A/B;
  - `POCKET_THREADS` stays 2 unless Q14 shows otherwise.
- **Voice-ahead (B9) takes stage 1 off the critical path.** At 2.83x, 40 films need 3.4 h of Pocket per day (§6.3); the risk is contention, not volume.
- **ASR pre-gate per sentence (B2)** catches garbles before the master is built. All 12 failed audits were text-completeness failures.
- **Repair:**
  - skip the master rebuild when no chunk changed;
  - keep failed ASR output;
  - `redo_voice` becomes a bridge endpoint under the lock (B13).
- **Model:** the full Pocket model stays. Smaller models (7M/18M/_refl/int8) only if all of these hold (B12): ECAPA ≥0.748, WER ≤2.8%, no repeats, and the user approves after listening.

### 4.7 Stage 3

1. **CPU tokens (B3): 10 of 16 logical CPUs** (encode 4, decode 2, HyperFrames 2, 3D 2). No class exceeds its limit in `system_speed_profile.json`. The other 6 CPUs are left for Pocket, the bridge, LLM I/O and the OS.
2. **One ffmpeg per source (B4).** Batched frame grabs for:
   - `_frame_at` (runner.py:755) and `_grid_frame` (runner.py:2536);
   - `_contact_frame` (sources.py:2278) and `_contact_sample` (sources.py:2322).
   Equivalence: SSIM ≥0.999.
3. **HyperFrames.**
   - The installed 0.8.181 is called directly (done, 137ee01).
   - The preset/CRF A/B and the 0.8.184 test only count if SSIM ≥0.999 (B5).
   - Fast-capture stays off (measured slower).
4. **3D still pre-check (B6).** One still frame is judged by the unchanged visual_fit review before the clip is rendered; a FAIL goes to the ladder. Today 59–83% of 3D shots fail.
5. **Feasibility gate before the MILP (A2).** It raises `ALLOCATION_SHORT:<category>:<have>/<need>` instead of an HTTP 500. The planner keeps its rule: "ratios were not silently changed" (planning.py:1319).
6. **Fallback ladder (A5).**
   - Weather, radar, map and diagram beats never route to 3D.
   - After 2 FAILs with the same review signature, the shot moves VIDEO → PHOTO → CARD → MOTION.
   - The breaker is persisted per film; G-Labs has its own breaker.
7. **Supply instead of ratio changes (A2).** Direct photo APIs with credits; in-process top-up (the `seed_photos.py` logic); a wider VIDEO catalog through `yt_gate`.
8. **Prescan as sources arrive, and reruns reuse the pre-pipeline (B8).** Duplicate prescans are already fixed (e936d45).
9. **Measurement.** Timers for the untimed 25–30% (A10); governor waits and tokens in events (A9).

### 4.8 Storage

- **Per film on C:**: 5.4 GB today; at most 0.3 GB after A3, once the delivery's sha256 verifies. Kept: plan, EDL, report, voice master and credits. Raw sources, renders and chunks are moved or removed by a retention policy that the user sets.
- **Delivery:**
  - built in a staging folder outside OneDrive, then moved; this avoids sync locks (the PermissionError at delivery.py:147 is swallowed today);
  - one root per channel;
  - a sha256 manifest.
- **yt_cache:** an LRU byte cap, without touching `bucket.json` or pacing.
- **Archive:** 71.2 GB/day at 40/day, about 1 TB per 14 days. The target is a user decision: external disk, Storage Box (price not checked), or delete after publish.

### 4.9 Observability

- **Q1 sampler**, recording:
  - CPU by role and `\Memory\Page Reads/sec`;
  - per-process faults and working sets; free RAM; pagefile;
  - accepted shots per hour and MSPS;
  - NIC bytes sent and C: free;
  - solo wall-minutes per film-minute;
  - tokens per film per lane.
- **A9 events:** governor slot waits, token usage per call, BBC cut-slot waits, and `yt_gate` calls per film.
- **A10:** timers for the untimed 25–30% of worker time.
- **Ledger daily report:**
  - films started and delivered;
  - failures by class;
  - manual runs and idle share;
  - delivered mix and PARTIAL count;
  - tokens per lane and disk;
  - remote share and fallbacks.

### 4.10 Claude's role

- Claude is woken only for `unknown` and `code_bug` classes. It reads `status.json`, not raw logs.
- Parallel items run as one Workflow per batch, with explicit models: Opus only for design and judgement, Sonnet for code, Haiku for scans.
- Maps are passed by file reference, and role agent files limit the tool surface (T3, T4).
- T14 tracks Claude tokens per delivered film.

---

## 5. Placement and cost

| Service | Host | Reason |
|---|---|---|
| Ledger, admission, classifier, sampler, supervisor, preflight | PC | Single writer next to the bridge; needs the process table and local files. The VDS is reached through a DERP relay |
| Bridge, stage workers, NVENC, QC, 3D, ffmpeg | PC | Local media and NVENC. The GPU averages 11%, so a rented GPU buys nothing |
| Pocket TTS | PC | FIFO plus voice-ahead; ~3.4 h/day at full speed |
| yt_gate and Firefox cookies | PC | The YouTube session lives in Firefox here; one shared budget |
| G-Labs API | PC (local API) | Shared with SkullStudio; daily budget (B14) |
| SearXNG and photo APIs | PC (Docker) | A move is considered only in C12, after an image-search test |
| 9router (Flash) and GPT gateway | VDS 100.104.78.117 (existing) | Unchanged; inventory in C12, direct path in C13 |
| HyperFrames MOTION/CARD worker | Hetzner AX42, only if gate C1 shows CPU binds | Offloads the heaviest child processes. The PC keeps the slot, the NVENC re-encode and QC; local fallback |
| Archive | User decision | 1 TB per 14 days at 40/day |

| Cost item | Amount | When |
|---|---|---|
| PC | €0 | now |
| VDS | existing | now |
| Hetzner AX42 | €99/month + €49 setup, about €0.08 per film at 1,200 films/month (research map price, 2026-10-30; re-check before ordering) | only after C1 says CPU |
| 32 GB RAM (2×16 GB or 1×32 GB DDR4-3200 SODIMM) | one-off, not priced | only after C1 says paging |
| Archive storage | not priced | after A3 policy |
| Paid LLM lane | $2.9–11.2 per film, $3.5k–13.5k per month at 1,200 films | only if free or shared lanes end (C3, C4) |

**Rejected hosting options**

| Option | Reason |
|---|---|
| Hetzner GEX GPU servers (research map: €214/month + €209 setup), Vast, RunPod | The GPU is not binding (11% mean), and NVENC on rented GPUs is unverified |
| Hetzner CCX33 (€138.99) | Price: 32 GB of dedicated vCPU against the AX42's 64 GB for less; the page also showed it unavailable |
| Contabo | Shared vCPU |
| Moving orchestration to the VDS (Argon) | DERP-relayed path; the single writer belongs next to the bridge |

---

## 6. Capacity math

### 6.1 Conventions

| Symbol | Meaning and value |
|---|---|
| λ | Arrival rate: 40 films ÷ 24 h = 1.67 films/h |
| shots | 190 accepted shots per film; 7,600 per day at 40/day |
| Usable machine-hours | 24 h × 0.85 (other load: Pocket, bridge, OS, SkullStudio) × 0.95 (uptime) = 19.4 h = 69,800 s |
| MSPS | Machine-seconds per accepted shot. Today's *estimate* is 13.9 s: 220 accepted shots per hour while 85% of the machine is available gives 3,600 × 0.85 ÷ 220 = 13.9 s |

### 6.2 Stage 3 CPU, the binding resource

| Films/day | Accepted shots | Machine time at 13.9 s | Load on 19.4 h |
|---|---|---|---|
| 10 | 1,900 | 1,900 × 13.9 = 26,410 s = 7.3 h | 38% |
| 20 | 3,800 | 52,820 s = 14.7 h | 76% |
| 30 | 5,700 | 79,230 s = 22.0 h | 113% |
| 40 | 7,600 | 105,640 s = 29.3 h | 151% |

**Target for 40/day**
- MSPS ≤ 69,800 s ÷ 7,600 = 9.2 s, a 34% cut.
- In throughput terms: 7,600 ÷ 24 h = 317 accepted shots per wall-hour (24-h mean), or 7,600 ÷ 22.8 h = 333 per hour while the line is up.

**Throughput while up = 3,600 × 0.85 ÷ MSPS**

| MSPS | Shots/h while up | Against 333/h |
|---|---|---|
| 13.9 | 220 | |
| 10.6 (D1 low end, ×0.76) | 289 | below: gate C1 trips |
| 9.2 | 333 | target |
| 6.5 (D1 high end, ×0.47) | 471 | |

**Where the 34% can come from** (each *estimate* is measured before it counts):
- **Waste.** 30–46% of render and anim seconds went to shots that never passed, and 59–83% of 3D shots failed. Addressed by A5 and B6.
- **Contention.** HyperFrames takes ~170 s contended against 35 s alone, and Pocket was paged out. Addressed by B3 and B1.
- **grid_prefilter** is 11–14% of step time; B4 targets −30% of that.
- **Duplicate prescans** (~10,300 s per batch) are already fixed by e936d45. This only shifts the baseline, and Q1 re-measures it.

### 6.3 Voice (Pocket, one serialized lane)

Demand at 40/day: 40 × 858 s = 34,320 s of audio.

| Pocket speed | Synthesis time per day | Share of 24 h |
|---|---|---|
| 2.83x (alone) | 34,320 ÷ 2.83 = 12,127 s = 3.4 h | 14% |
| 0.48x (aggregate on 2026-10-30) | 71,500 s = 19.9 h | 83% |
| 0.19x (contended) | 180,630 s = 50.2 h | 209% |

- **At 20/day and 0.19x:** 25.1 h, or 104%. Voice binds as early as Phase B unless contention is fixed (B1, Q14).
- **Repairs:** about 1.1 rounds per film × 17–100 s of resynthesis × 40 films = 0.2–1.2 h/day. That is small once garbles are caught early (B2).

### 6.4 HyperFrames (5 slots, `system_speed_profile.json`)

**Demand:** 20 MOTION × 1.35 attempts + 30 CARD × 1.3 attempts = 66 renders per film, or 2,640 per day.

**Slot capacity:** 5 × 86,400 = 432,000 slot-seconds per day.

| Scenario | Slot-seconds per day | Load |
|---|---|---|
| Contended, ~170 s per render | 2,640 × 170 = 448,800 | 104% |
| Solo (MOTION 35 s, CARD 20 s) | 40 × (27 × 35 + 39 × 20) = 40 × 1,725 = 69,000 | 16% |

- Each 20 s of render-step time spent outside the slot removes 2,640 × 20 ÷ 432,000 = 12 points of load.
- If B3 caps HyperFrames at 2 CPU tokens, capacity drops to 172,800 slot-seconds. Each render may then hold its slot for at most 172,800 ÷ 2,640 = 65 s on average. That is reachable only if contention falls toward the solo times; B3 measures this.
- **Conclusion:** HyperFrames is a symptom of stage-3 CPU contention, not an independent bottleneck. If gate C1 shows CPU binds, the AX42 offload (C2) is the lever.

### 6.5 G-Labs (ANIM)

40–92 assets per film against about 1,400 per night, shared with SkullStudio. The ~1,400 figure is anecdotal.

| Films/day | Assets | Load on 1,400 |
|---|---|---|
| 10 | 500–920 | 36–66% |
| 20 | 1,000–1,840 | 71–131% |
| 40 | 2,000–3,680 | 143–263% |

At 40/day, ANIM's share must shrink, or another asset source must be found (B14, C6). This is a supply decision, not an engineering one.

### 6.6 RAM and films in flight

**Films in flight (Little's law):**
- W, the time from admission to delivery, is 2.53–2.93 h; EP04 took 176 min = 2.93 h.
- L = λ × W = 1.67 × 2.53–2.93 = 4.2–4.9 films in flight.
- With tail admission counting tail films as 0.5, that is about 3.6 full films.

**Memory today:**
- About 5 films in flight left 1.6 GB free, 4.5 GB of pagefile in use, and Pocket paged out.
- Bridge private memory is 6.4 GB for those films, roughly 1.3 GB per film (*estimate*). Pocket adds 3 GB, plus children: Chrome, ffmpeg, the 3D renderer.

**The trap:** W grows with L under contention. Adding film slots without first cutting MSPS makes every film slower. The order is:
1. cut MSPS (Phase B);
2. measure paging (Q1);
3. add slots (C8) or RAM (C1).

### 6.7 LLM lanes

**Flash** (9router, 15 slots)
- Demand: 988–1,505 calls per film (Flash + flash_review + gdirect; EP04: 884 + 87 + 17; EP03: 1,334 + 149 + 22), so 39.5k–60.2k calls per day at 40/day.
- Theoretical capacity: 15 × 86,400 ÷ 8.5 s = 152k per day. Realistic: 76–99k (*estimate*, 50–65% use).
- Load: 26–39% of theoretical.

**After GPT ends**
- GPT calls move to Flash: 1,397–2,048 calls per film, or 55.9k–81.9k per day.
- That is 57–108% of the realistic Flash ceiling.

**GPT gateway** (4 slots; `GPT_SLOTS=4` in io.py:53 and :756)
- Demand: 357–543 calls per film, or 14.3k–21.7k per day.
- Capacity: 4 × 86,400 ÷ 14 s = 24.7k per day.
- Load: 58–88%, on a gateway that is shared and ending.

**Own Gemini keys:** about 46 successful calls per day. Not capacity.

**Paid exposure:** $2.9–11.2 per film if both shared lanes end (C4).

### 6.8 Other stages and services at 40/day

| Resource | Arithmetic | Load |
|---|---|---|
| Stage 2 | 38–174 s × 40 = 1,520–6,960 s = 0.4–1.9 h | light; LLM-bound |
| Stage 4 | 391 s × 40 = 15,640 s = 4.3 h | 18% of a day; B11 makes concurrent runs safe |
| YouTube calls | 4–12k per day against 41.7/min × 1,440 = 60k | 7–20%; concurrency 3 and cookie health bind first |
| Fact-check | 161–337 s × 40 = 1.8–3.7 h, serial | B10 targets ≤120 s per film |

### 6.9 Disk, archive and uplink

| Resource | Arithmetic | Result |
|---|---|---|
| C: today | 5.4 GB × 40 = 216 GB/day against 135.9 GB free | full in 135.9 ÷ 216 × 24 = 15.1 h; at 10/day (54 GB/day), full in 2.5 days |
| C: after A3 | 0.3 GB × 40 = 12 GB/day | stable with retention |
| Archive | 1.78 GB × 40 = 71.2 GB/day | 1.0 TB per 14 days |
| Uplink | 71.2 GB × 8 ÷ 86,400 s | 6.6 Mbit/s continuous for OneDrive, plus YouTube uploads (unmeasured) |

### 6.10 Binding constraint per phase

| Phase | Target | Binds first | Binds next | Evidence |
|---|---|---|---|---|
| A | ≤10/day | Failure handling and orchestration: 27% idle, ~14 manual runs, 6 of 9 stage-1 failures, 3 allocation crashes | C: disk (2.5 days at 10/day); source supply (SearXNG, photos) | §2.2, §2.4, §6.9 |
| B | 20/day | Stage-3 CPU at 76%, with Pocket under contention (0.19x means 104% at 20/day) | G-Labs at 71–131% | §6.2, §6.3, §6.5 |
| C | 30–40/day | Stage-3 CPU at 113–151% (gate C1) | G-Labs 143–263%; LLM after GPT ends 57–108%; RAM/paging (L = 4.2–4.9); archive and uplink (1 TB per 14 days, 6.6 Mbit/s); scripts and publishing (unknown) | §6.2–§6.9 |

---

## 7. Quality and variety safeguards

1. **Judges stay fixed.** Fixed judges and gates:
   - the voice audit, and the Gemini audio review (`SCR\documentary_voice_gemini_review.py`);
   - the GPT reviewer and visual_fit;
   - fact-check flags and QA thresholds.

   Changing any of them needs evidence from `TB\skull\judgeprobe\probe.py` and user approval. Items that touch a judge are flagged NEEDS_USER: B6, B10, C3 and C16.
2. **Speed changes must prove equivalence.**
   - Renders: SSIM ≥0.999 against current output (B4, B5, C2).
   - Audio: identical for the same seed, or ECAPA ≥0.748 and WER ≤2.8% (B1, B12).
   - Plans: `plan_diff.py` shows no change in category ratios (A2, B8).
3. **Use several runs.** Selection is nondeterministic: 15 of 17 shots differ between runs on the mini film. Use at least 2 runs per side and compare distributions with `diff_films.py`.
4. **Mix.** The target mix holds; the planner never changes ratios silently. Deviations come from fallbacks, short supply and PARTIAL acceptance, and the fix is supply (A2). The daily report shows the delivered mix per film.
5. **PARTIAL acceptance is tracked per film.** Throughput work must not raise it.
6. **Variety.**
   - Shot lengths within a scene stay uneven (ff26bfe).
   - A per-channel source ledger blocks reuse of the same origin for N days (C5).
   - Identity packs and a template ledger per channel stop the same CARD/MOTION families repeating in consecutive films (C6).
   - Channel style profiles vary CTA and pauses per film.
7. **Value.**
   - Fact-check before delivery (B10).
   - Credits for every non-YouTube asset (A2).
   - Synthetic-content disclosure (C11).
   - Real footage first; no logo or watermark removal (Q13).
8. **Voice identity.** A model or voice changes only after the user listens (B12, C7).
9. **Buffer before publishing.** Finished films are held for QA before they publish (C9).
10. **Never:**
    - bypass `yt_gate`;
    - raise NVENC or slot limits without approval;
    - print keys;
    - rotate keys or projects to dodge quotas. Use one project with a quota extension (C9).

---

## 8. Migration protocol and phase gates

### 8.1 Change path

testbench copy → DIFF_MINI (≥2 runs per side) → canary → production.
- The testbench copy is `TB\scripts`, started by `TB\start_test_bridge.ps1` on bridge :8199.
- DIFF_MINI is `TB\films\DIFF_MINI`, compared with `diff_films.py` and `plan_diff.py`.
- The canary is one production film, watched by the ledger.

### 8.2 How each kind of change is deployed

| Kind of change | Deploy | Rollback |
|---|---|---|
| `documentary_materials.*`, `adaptive_governor` | Hot-reloaded on the next stage POST. Until A1 lands, a reload resets limits, so deploy between stage starts | `git revert`; the next stage POST picks it up |
| Bridge file | It reloads its own source (`_bridge_source_changed()` in do_POST). The host binding, new routes in the running server's handler (unverified) and server settings need a restart | `git revert` plus a restart in a drain window |
| Orchestration Python (drive.py, queue_films.py, supervisor.py, ledger) | Running processes keep old code; new launches use new code | revert in the Kanallar git (Q9) |
| Bash scripts | Never edit a running `.sh`, because bash reads it incrementally. Write a new file (`run_when_free2.sh`) | keep the old file |
| Pocket, G-Labs, SearXNG, bridge restarts | Drain window only: ledger drain mode, then wait until in-flight films are in stage 4 or done | restart the previous version |
| Remote lanes (AX42, paid LLM) | JSON switch read per call; shadow, then 10%, then 100% | switch off |

### 8.3 Drain windows

- At 40/day a drain costs 2–3 h of throughput, so restarts are batched into one maintenance window. The user picks the time.
- Items marked NEEDS_IDLE wait for that window.

### 8.4 Phase gates

| Gate | Entry | Exit (all must hold) | Measured by | If it fails |
|---|---|---|---|---|
| Phase 0 | now | Wave W0-1 merged; Q1 baseline of 24 h; no manual run caused by SearXNG, docker or exit codes in 2 batches | Q1 report, batch.log | fix the item; heavy Phase A items wait |
| Phase A | Phase 0 exit (A1 and A4 may start earlier) | 3 consecutive days with: 0 manual runs; 0 SearXNG failures; C: growth <10 GB/day; Flash peak ≤15; ledger shadow agreement ≥95%; 10 films/day | ledger daily report, Q1 | stay at 10/day; classify the remaining manual runs |
| Phase B | Phase A exit | 3 days at 20/day; voice first-audit pass ≥80%; idle <10%; Pocket ≥1.8x under load; mix within ±5 pts; PARTIAL not above baseline; judges unchanged | same, plus A9 | stay at 20/day |
| Gate C1 | Phase B exit | Three 24-h days at ≥317 accepted shots/h means no purchase. Otherwise: paging-bound → 32 GB RAM; CPU-bound → AX42 | Q1 | user decision (money) |
| Phase C | C1 decision; G-Labs budget, LLM plan, scripts and publishing in place | 40/day for 7 days with judges unchanged; 0 reused origins per channel within N days; publishing running | ledger, C5 | hold at the highest stable rate |

---

## 9. OSS building blocks

Links marked † are standard documentation added by the architect and were not re-checked on 2026-10-30. The others come from this workflow's research map.

| Need | Building block | Decision | Link |
|---|---|---|---|
| Ledger store | Python `sqlite3` with WAL | Adopt: stdlib, no daemon, works on Windows | https://docs.python.org/3/library/sqlite3.html †, https://www.sqlite.org/wal.html † |
| Queue frameworks | Huey (sqlite storage), taskito, Temporal dev server, Hatchet Lite, Procrastinate (also DBOS, Celery, RQ) | Rejected: one table is enough; they add RAM or services, have unclear Windows support, or need fork() | https://huey.readthedocs.io/en/latest/contrib.html, https://pypi.org/project/taskito/0.16.3/, https://docs.temporal.io/develop/run-a-development-server.md, https://docs.hatchet.run/llms/self-hosting/hatchet-lite.md, https://github.com/procrastinate-org/procrastinate |
| Process and RAM metrics | psutil; typeperf counters | Adopt in Q1 | https://psutil.readthedocs.io/ †, https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/typeperf † |
| Service restarts | Task Scheduler plus a PowerShell wrapper | Adopt in A7; registration is a user decision | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks † |
| Frame grabs | ffmpeg input seeking, one process per source; NVDEC as an A/B arm | Adopt in B4 | https://trac.ffmpeg.org/wiki/Seeking, https://ffmpeg.org/pipermail/ffmpeg-trac/2018-January/043040.html, https://forums.developer.nvidia.com/t/should-i-use-gpu-for-generating-thumbnails-by-ffmpeg/79386 |
| NVENC session limits | Consumer GPU session context | Rule unchanged; no driver patch | https://tomshardware.com/news/nvidia-increases-concurrent-nvenc-sessions-on-consumer-gpus |
| HyperFrames | Engine docs, v0.8.184 release, issue #521 | A/B in B5; a version change is a user decision | https://hyperframes.heygen.com/packages/engine, https://github.com/heygen-com/hyperframes/releases/tag/v0.8.184, https://github.com/heygen-com/hyperframes/issues/521 |
| Render concurrency reference | Remotion concurrency notes | Reference for B3 sizing | https://www.remotion.dev/docs/terminology/concurrency |
| TTS | Pocket TTS (Kyutai) | Keep; smaller models only through B12 | https://github.com/kyutai-labs/pocket-tts, https://kyutai-labs.github.io/pocket-tts |
| ASR | faster-whisper | Already used; per-sentence pre-gate in B2 | https://github.com/SYSTRAN/faster-whisper † |
| Search | SearXNG | Keep; health check on image results (Q6) | https://docs.searxng.org/ † |
| Photo sources | Wikimedia Commons, NASA Images, Library of Congress, Internet Archive, Openverse | Adopt in A2; licence policy is a user decision | https://commons.wikimedia.org/w/api.php, https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf, https://www.loc.gov/apis/json-and-yaml/, https://archive.org/advancedsearch.php, https://api.openverse.org/v1/ |
| Publishing | YouTube Data API videos.insert; quota cost table | C9, a user decision | https://developers.google.com/youtube/v3/docs/videos/insert †, https://developers.google.com/youtube/v3/determine_quota_cost † |
| Policy | YouTube altered or synthetic content disclosure; YouTube policy page cited by the research map | C11 | https://support.google.com/youtube/answer/14328491, https://support.google.com/youtube/answer/1311392 |
| Network | Tailscale connection types (direct or DERP) | C13 | https://tailscale.com/kb/1257/connection-types |
| Hosting | Hetzner AX42 (conditional); cloud general purpose and GEX (rejected) | C1, C2 | https://www.hetzner.com/dedicated-rootserver/ax42/, https://www.hetzner.com/cloud/general-purpose, https://www.hetzner.com/dedicated-rootserver/gex44/ |
| Archive | Hetzner Storage Box | Candidate; price not checked | https://www.hetzner.com/storage/storage-box/ |
| Pipeline examples | GitHub faceless-channel topic; a write-up of a 108-video auto-publishing pipeline | Reference only | https://github.com/topics/faceless-channel, https://dev.to/sakshi_bansal_02300624579/how-i-built-a-python-pipeline-that-publishes-youtube-videos-automatically-108-videos-proven-1536 |

---

## 10. Decisions needed from the user

| ID | Decision | Items |
|---|---|---|
| D1 | Re-base the "≤15 min per film" target. It was set for 4–5-minute films; for 15-minute films, planning alone takes 18 min. Proposed instead: accepted shots per hour, plus solo wall-minutes per film-minute (4.8 today, TOPIC_2) | Q1, Q11 |
| D2 | Licence allowlist for direct photo APIs, and the credit format | A2 |
| D3 | Storage: delivery root per channel, retention period, what is kept after delivery, archive target | A3 |
| D4 | Keep the free-tier Gemini key lane as burst and backup, or retire it (terms, training use) | Q12 |
| D5 | Stop sending `remove_logo`, and what to do if G-Labs assets then show marks | Q13 |
| D6 | Fallback-ladder order, ANIM share and G-Labs daily shares between the two lines | A5, B14 |
| D7 | Ledger cutover, Task Scheduler registration for the ledger and the service wrapper, retiring `queue_films.py` and `run_when_free*.sh`, and the local 9router binding 0.0.0.0:20128 | A4, A7 |
| D8 | Is Dify still used? Yes: keep the bridge on 0.0.0.0 and the user adds a firewall rule. No: bind 127.0.0.1 | Q7 |
| D9 | Tail admission and film slots 3 → 4–5 | B7, C8 |
| D10 | New or changed gates: 3D still pre-check, fact-check precision and its position, a top-3 single review call and review trimming, judge replacements when GPT ends | B6, B10, C16, C3 |
| D11 | HyperFrames version change; Pocket smaller models (gated weights, licence, listening) | B5, B12 |
| D12 | Money: 32 GB RAM or AX42 (€99/month + €49), a paid LLM lane, archive storage | C1, C2, C4, A3 |
| D13 | Channels: the 4 channels (10 films each), "Isaac", voice per channel, identity packs, who writes 40 scripts a day, publishing OAuth and quota extension, disclosure policy | C6, C10, C9, C11 |
| D14 | Access for a VDS inventory, and network changes for a Tailscale direct path | C12, C13 |
| D15 | Claude setup: role agent files, settings.json cleanup, durum.py hook, rtk, memory consolidation | T3, T9, T10, T11, T13 |
| D16 | Hygiene deletions; edits to `Engineered\CLAUDE.md`; one KEY.txt path | Q10, Q11 |
| D17 | A maintenance window for drain-window restarts | NEEDS_IDLE items |

---

## 11. Unverified

| ID | Point | Resolved by |
|---|---|---|
| U1 | 13.9 machine-seconds per accepted shot and ~220 shots/h are estimates | Q1 |
| U2 | The realistic Flash ceiling (76–99k/day) is an estimate; 9router's own limits are not inventoried | C12, A9 |
| U3 | G-Labs ~1,400 assets per night is anecdotal; its cap and terms are unknown | B14 |
| U4 | Whether HyperFrames accepts a CRF override; the status of issue #521; how 0.8.184 behaves | B5 |
| U5 | The root cause of EP05's allocation failure (41 photos) | A2 |
| U6 | Where the live bridge writes its log (silent since 11:02) | Q7, A7 |
| U7 | Whether `_reload_bridge_itself()` (bridge :142) swaps the handler class of the running server | B13, C14 |
| U8 | Which import re-registers yt-dlp's PoTokenProvider after a reload. The name does not appear in any `.py` under SCR | A1 |
| U9 | AX42 price and availability and rented NVENC capability, as read on 2026-10-30; the Storage Box price was not checked | C1, C2 |
| U10 | Uplink capacity and YouTube upload sizes | Q1, C9 |
| U11 | Which 429 kind (per minute or per day) marked the 23 Gemini pairs spent | Q12 |
| U12 | Whether the hash in `tests/test_media_memory.py:115` is stale. The test is too heavy to run while films run | Q10 (NEEDS_IDLE) |
| U13 | Whether `picture_fit.py` replaces branch a99137 | Q10 |
| U14 | The D1 savings factors (×0.76 to ×0.47) and per-lever gains | B3–B6 measurements |
| U15 | The 25–30% of worker time that is untimed | A10 |
| U16 | Script supply and publishing capacity for 40/day | C9, C10 |
| U17 | The token-economy mechanisms behind G2, G5, G6 and G10 are untested; the chars-per-token calibration is approximate | T3, T6, T7, T10 |
| U18 | The GPT model string: SISTEM.md says `gpt-6-sol`, while the code pins `gpt-6.1-sol` (`documentary_voice_step2.py:279`, `documentary_voice_audit.py:20`) | A8, Q11 |
| U19 | Whether `documentary_voice_step2.py:319` (local 9router 127.0.0.1:20128, no traffic since 10-24) is a live fallback | A8 |
