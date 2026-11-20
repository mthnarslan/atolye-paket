# 40 films per day: work plan

**About this plan**
- **Date:** 2026-10-30.
- **Companion document:** `docs\ARCHITECTURE_40_PER_DAY.md` in this folder. "Arch §x" below refers to its sections.
- **Status:** plan only. No item has started and nothing is committed.
- **How to use it:**
  - The dispatching (main) session runs the waves in the order given in §3.
  - Each agent gets its item's brief verbatim, plus the path of the wave's baseline runs.
  - Items flagged NEEDS_USER wait for the user's answer.
  - Items flagged NEEDS_IDLE run only in a drain window.
- **Counts:**
  - 68 IDs, of which 66 are active (T1 and T12 are merged into other items).
  - NEEDS_USER: 35, plus 1 conditional. NEEDS_IDLE: 11.
  - 19 rejected gaps (§7).

**Path shorthands used outside the briefs.** The briefs use full paths.

| Shorthand | Path |
|---|---|
| DM | `C:\Users\meteh\.gemini\scripts\documentary_materials` (production repo) |
| SCR | `C:\Users\meteh\.gemini\scripts` |
| ENG | `C:\Users\meteh\Kanallar\Engineered` |
| TB | `C:\Users\meteh\testbench` |
| VL | `C:\Users\meteh\codex-repo-tests\voice-lab` |

---

## 1. Standing rules for every agent

Every brief starts by pointing here. These rules apply to every item.

1. **Scope**
   - Do only your item.
   - Write only the files listed for it, plus their testbench copies and new tests.
   - If you need another file, stop and report it, because another item may own that file in the same wave.
2. **Judges are fixed**
   - Never relax QA thresholds, judge prompts or models, tests, `yt_gate` pacing, or NVENC and slot limits (`C:\Users\meteh\.gemini\scripts\system_speed_profile.json`).
   - Tightening is allowed only where the item says so.
   - If evidence says a judge is wrong, stop and report the frame or measurement.
3. **Testbench first**
   - Change and test in `C:\Users\meteh\testbench\scripts`. It mirrors `C:\Users\meteh\.gemini\scripts`; diff the files you touch before you start.
   - Test through the test bridge on :8199, started by `C:\Users\meteh\testbench\start_test_bridge.ps1`.
   - Never send test traffic to the production bridge on :8099.
   - Production gets the same diff only after the test passes.
4. **Bench lock (the testbench is shared)**
   - Hold `C:\Users\meteh\testbench\.bench_lock` while you edit testbench copies or run films. Create it with mkdir and write your item ID and PID inside.
   - Prepare code and unit tests before taking the lock, and release it when done.
   - Start a bench film only if free RAM is at least 3 GB. Production comes first.
5. **Measure properly**
   - Use the mini film `C:\Users\meteh\testbench\films\DIFF_MINI`, and compare with `C:\Users\meteh\testbench\diff_films.py` and `plan_diff.py`.
   - Shot selection differs from run to run (15 of 17 shots on the mini film), so use at least 2 runs per side (more where the item says). Report every run, not just the best one.
   - Per wave, the dispatcher makes 2 baseline runs of the current production code in `C:\Users\meteh\testbench\baselines\<wave>\`. Reuse them.
6. **Drain windows**
   - Items flagged NEEDS_IDLE run only in a drain window. These are restarts of the bridge, Pocket or other shared services, and heavy benchmarks.
   - The dispatcher opens the window once in-flight films have reached stage 4 or finished.
7. **Hot reload**
   - `documentary_materials.*` and `adaptive_governor` reload on the next stage POST.
   - Keep module-level locks, semaphores and caches with the `globals().get(...)` pattern (`bbc_library.py:534`).
   - Python processes that are already running keep the old code.
   - Never edit a running `.sh` file; write a new file instead.
8. **Secrets**
   - Never print, log, copy or commit keys.
   - Do not open `C:\Users\meteh\OneDrive\Desktop\KEY.txt`, `C:\Users\meteh\Desktop\KEY.txt` or `C:\Users\meteh\Kanallar\ortak-site-anahtarlar.txt` unless your item says so.
   - Identify keys by their last four characters only. Never put secrets in URLs.
9. **Never:**
   - bypass `yt_gate`;
   - add logo or watermark removal;
   - run Sopro on the GPU;
   - delete data (list it instead);
   - create accounts, enter payment details, or accept terms on the user's behalf;
   - change Claude settings, hooks, memory or CLAUDE.md files, unless the item is flagged NEEDS_USER and the user approved the exact diff.
10. **Language.** Code, comments, logs and commit messages are in English. Production output stays English.
11. **Commits**
    - Commit only when the dispatcher says so: one commit per item, with a message that describes the change in behaviour.
    - End the message with the attribution line the dispatcher gives you. Never push.
12. **Shared notes**
    - Do not edit `C:\Users\meteh\Kanallar\SISTEM.md` (item Q11 is the only exception), any `DURUM.md` file, or the Ortak Atölye site.
    - Instead, return a proposed one-line SISTEM.md entry and, for shared improvements, the measured numbers for a site card. The dispatcher writes them.
13. **Context economy**
    - Use Haiku sub-agents for listing and scans, Sonnet for code and tests, and Opus only for design or judgement.
    - Pass large context by file path. Run long commands in the background.
14. **Time budget.** Each brief states one. If you exceed it, stop and report what is done, the numbers so far, and the blocker.
15. **What to return (≤15 lines):**
    - the files you changed;
    - every test run with its numbers, before and after;
    - whether the acceptance criterion was met;
    - risks, and the rollback command;
    - a proposed SISTEM.md line.

---

## 2. Phase overview

Phase gates and their measurement are in Arch §8.4. Capacity arithmetic is in Arch §6.

| Phase | Goal | Items | Exit criteria (all must hold) | Binds at this phase |
|---|---|---|---|---|
| 0 | Quick safe wins: honest signals and measurement | Q1–Q14, plus A10 and A7 scheduled in Phase 0 waves | Wave W0-1 merged; Q1 24-h baseline exists; no manual run caused by SearXNG, docker or exit codes in 2 batches | – |
| A | A reliable 10 films/day | A1–A10 | For 3 days: 0 manual runs; 0 SearXNG failures; C: growth <10 GB/day; Flash peak ≤15; ledger shadow agreement ≥95%; 10 films/day | Failures and orchestration (27% idle, ~14 manual runs); C: disk; source supply |
| B | 20 films/day on the same hardware | B1–B14 | 3 days at 20/day; voice first-audit pass ≥80%; idle <10%; Pocket ≥1.8x realtime under load; mix within ±5 pts; PARTIAL not above baseline; judges unchanged | Stage-3 CPU at 76%; Pocket contention (0.19x means 104%); G-Labs at 71–131% |
| C | 30–40 films/day | C1–C16 | Gate C1 decided; 40/day for 7 days with judges unchanged; 0 reused origins per channel within N days; publishing and intake running | Stage-3 CPU at 113–151% (gate C1); G-Labs at 143–263%; LLM after GPT ends (57–108%); RAM and paging; archive and uplink; scripts and publishing |
| T | Claude token economy, in parallel with the other phases | T2–T14 | Commander weighted tokens per delivered film down ≥40% against 2026-10-30 (target, measured by T14); no supervisor re-arm wake-ups | – |

---

## 3. Waves and file ownership

**How waves run**
- Waves run in the order below, and every item in a wave writes a disjoint set of files.
- An item may start before its wave only if two things hold:
  - its dependencies are merged;
  - no running item writes any of its files.
- Each item also edits the testbench copies of its own files, and only those.

| Order | Wave | Items | Starts when |
|---|---|---|---|
| 1 | W0-0 | Q9 | now |
| 2 | W0-1 | Q1, Q2, Q3, Q4, Q5, Q6, Q8, Q12, A10 | W0-0 merged |
| 3 | W0-2 | Q10, Q11, Q13 | W0-1 merged (Q11 records it) |
| 4 | W0-idle | Q7, Q14, A7 | first drain window |
| 5 | WA-1 | A1, A3, A4, A6, A8 | W0-2 merged. A4, A6 and A8 may start with W0-1; A3 may start once Q2 is merged |
| 6 | WA-2 | A2, A9 | WA-1 merged |
| 7 | WA-3 | A5 | WA-2 merged |
| 8 | WB-1 | B1, B3, B7, B10, B12, B14 | Phase A exit. B10 may start after Q6; B12 after Q14 |
| 9 | WB-2 | B2, B4, B5, B9, B11 | WB-1 merged |
| 10 | WB-3 | B6 | WB-2 merged |
| 11 | WB-4 | B8 | WB-3 merged |
| 12 | WB-idle | B13 | drain window after WB-1 |
| 13 | WC-1 | C1, C3, C4, C5, C7, C9, C10, C12, C13 | Phase B exit. C9, C10 and C12 may start earlier once the user decides |
| 14 | WC-2 | C2, C8, C15 | WC-1 merged; C2 only if C1 says CPU |
| 15 | WC-3 | C6, C11, C16 | WC-2 merged |
| 16 | WC-idle | C14 | drain window |
| any | WT-1 | T2, T4, T5, T6, T7, T8, T14 | any time after W0-0 (all new files) |
| any | WT-user-1 | T3, T9, T10, T13 | user approval |
| any | WT-user-2 | T11 | after T9 (same file) |

**Ownership matrix**

| Wave | Item | Files written |
|---|---|---|
| W0-0 | Q9 | new `.gitignore` and `.git` in `C:\Users\meteh\Kanallar`, VL and TB |
| W0-1 | Q1 | TB\prod_sampler\ (new) |
| W0-1 | Q2 | TB\disk_report\ (new) |
| W0-1 | Q3 | ENG\tools\drive.py, ENG\tools\queue_films.py, TB\drive_stub\ (new) |
| W0-1 | Q4 | ENG\tools\run_when_free2.sh (new) |
| W0-1 | Q5 | ENG\tools\supervisor.py |
| W0-1 | Q6 | DM\sources.py (ensure_searxng, up, searxng_images only), DM\tests\test_searxng_health.py (new) |
| W0-1 | Q8 | DM\render.py, DM\tests\test_render_range_source.py (new) |
| W0-1 | Q12 | DM\gemini_keys.py, DM\tests\test_gemini_keys_429.py (new) |
| W0-1 | A10 | DM\runner.py (timers only) |
| W0-2 | Q10 | TB\hygiene\ (new) |
| W0-2 | Q11 | `C:\Users\meteh\Kanallar\SISTEM.md`, ENG\CLAUDE.md |
| W0-2 | Q13 | DM\anim.py, DM\runner.py (:1743 only), `C:\Users\meteh\SkullStudio\pipeline\gen2.py` (:73 only) |
| W0-idle | Q7 | SCR\documentary_native_bridge.py |
| W0-idle | Q14 | TB\pocket_ab\ (new) |
| W0-idle | A7 | `C:\Users\meteh\Kanallar\services\` (new) |
| WA-1 | A1 | SCR\adaptive_governor.py, DM\resources.py, DM\runner.py, DM\io.py, DM\recovery.py, DM\three_render.py, DM\sources.py, DM\tests\test_reload_state.py (new) |
| WA-1 | A3 | DM\delivery.py, DM\yt_cache.py, DM\retention.py (new), DM\tests\test_retention.py (new) |
| WA-1 | A4 | ENG\ledger\ (new) |
| WA-1 | A6 | `C:\Users\meteh\Kanallar\preflight.py` |
| WA-1 | A8 | SCR\documentary_voice_step2.py, SCR\documentary_voice_audit.py, SCR\documentary_voice_audit_config.json, SCR\ask_frontier_models.py |
| WA-2 | A2 | DM\sources.py, DM\planning.py, DM\runner.py, DM\photo_sources.py (new), DM\credits.py (new), new tests |
| WA-2 | A9 | SCR\adaptive_governor.py, DM\io.py, DM\bbc_library.py, DM\yt_gate.py |
| WA-3 | A5 | DM\planning.py, DM\runner.py, DM\anim.py |
| WB-1 | B1 | SCR\documentary_voice_engine.py, SCR\sopro_voice_client.py (lock and URL env only), VL\pocket-tts\pocket_serve.py, VL\Start-Pocket.ps1 |
| WB-1 | B3 | SCR\adaptive_governor.py, SCR\system_speed_profile.json, DM\resources.py, DM\motion.py, DM\cards.py, DM\three_render.py, DM\render.py |
| WB-1 | B7 | ENG\ledger\admit.py |
| WB-1 | B10 | SCR\documentary_factcheck.py |
| WB-1 | B12 | TB\pocket_models\ (new) |
| WB-1 | B14 | DM\glabs_budget.py (new), DM\anim.py |
| WB-2 | B2 | SCR\documentary_voice_pregate.py (new), SCR\documentary_voice_engine.py |
| WB-2 | B4 | DM\runner.py, DM\sources.py |
| WB-2 | B5 | DM\motion.py, DM\cards.py, TB\hf_ab\ (new) |
| WB-2 | B9 | ENG\ledger\voice_queue.py (new), ENG\ledger\daemon.py |
| WB-2 | B11 | DM\render_stage.py, DM\delivery.py |
| WB-3 | B6 | DM\three_render.py, DM\runner.py, TB\skull\judgeprobe\ (new cases) |
| WB-4 | B8 | DM\scan_cache.py, DM\footage.py, DM\runner.py |
| WB-idle | B13 | SCR\documentary_native_bridge.py, SCR\documentary_voice_repair.py |
| WC-1 | C1 | TB\gate_c1\ (new) |
| WC-1 | C3 | TB\gpt_end\ (new), DM\io.py (approved routes only) |
| WC-1 | C4 | TB\paid_lane\ (new) |
| WC-1 | C5 | DM\source_ledger.py (new), DM\reservations.py |
| WC-1 | C7 | `C:\Users\meteh\SkullStudio\pipeline\` gen2.py, batch.py, gen_newposes.py, common.py, build8 script |
| WC-1 | C9 | ENG\publish\ (new) |
| WC-1 | C10 | ENG\intake\ (new) |
| WC-1 | C12 | TB\vds_inventory\ (new) |
| WC-1 | C13 | TB\net_path\ (new) |
| WC-2 | C2 | DM\remote_render.py (new), DM\motion.py, DM\cards.py, `C:\Users\meteh\Kanallar\services\hf_worker\` (new) |
| WC-2 | C8 | ENG\ledger\admit.py, DM\bbc_library.py |
| WC-2 | C15 | DM\runner.py, DM\sources.py |
| WC-3 | C6 | DM\profiles.py, DM\template_ledger.py (new), DM\cards.py, DM\motion.py, channel pack files (new) |
| WC-3 | C11 | ENG\publish\metadata.py, DM\delivery.py |
| WC-3 | C16 | DM\runner.py, DM\io.py |
| WC-idle | C14 | SCR\documentary_native_bridge.py, ENG\ledger\stage_client.py |
| WT-1 | T2 | ENG\RUNBOOK_BATCH.md (new) |
| WT-1 | T4 | `C:\Users\meteh\Kanallar\workflows\` (new) |
| WT-1 | T5 | TB\token_audit\brief_ab\ (new) |
| WT-1 | T6 | TB\token_audit\wrapup\ (new) |
| WT-1 | T7 | TB\token_audit\tools_load\ (new) |
| WT-1 | T8 | ENG\tools\wait_film.py (new) |
| WT-1 | T14 | TB\token_audit\per_film\ (new) |
| WT-user-1 | T3 | `C:\Users\meteh\.claude\agents\` (new) |
| WT-user-1 | T9 | `C:\Users\meteh\.claude\settings.json` |
| WT-user-1 | T10 | `C:\Users\meteh\.claude\hooks\durum.py` |
| WT-user-1 | T13 | the two memory folders under `C:\Users\meteh\.claude\projects\` |
| WT-user-2 | T11 | `C:\Users\meteh\.claude\settings.json` |

---

## 4. Work items

Each item lists: why (the bottleneck it targets and the expected measured gain), files, dependencies, wave, size and model, flags, test, acceptance, risk and rollback, and a self-contained brief of at most 150 words.

### Phase 0: quick safe wins

#### Q1. Production sampler and token ledger
- **Why:** Every capacity number in this plan rests on estimates (13.9 machine-seconds per accepted shot, about 220 shots/h). Paging and CPU by role are not measured in production: 4.5 GB of pagefile was in use, and Pocket sat at a 2 MB working set. **Gain:** the baseline every later item is judged against. Gate C1 needs 3 days of it.
- **Files:** TB\prod_sampler\ (new). Read-only everywhere else.
- **Depends on:** –. **Group:** W0-1. **Size/model:** M / sonnet. **Flags:** –
- **Test:**
  - 30 minutes beside production. Per-process CPU and RAM must match a psutil snapshot within ±5%.
  - EP04 call counts must exactly match its event logs: flash 884, codex 409, flash_review 87, gdirect 17.
  - Sampler overhead measured from its own process times.
  - Then one 24-h run.
- **Accept:**
  - A 24-h report with: CPU by role; page reads/s; per-process hard faults and working sets; free RAM; pagefile; NIC bytes sent; C: free; accepted shots per hour; machine-seconds per accepted shot; solo wall-minutes per film-minute; calls and tokens per film per lane ("n/a" where no usage record exists, until A9).
  - Overhead below 1% CPU and below 100 MB RAM.
- **Risk / rollback:** read-only; stop the process.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Build a read-only production sampler in new folder C:\Users\meteh\testbench\prod_sampler\ (reuse ideas from C:\Users\meteh\testbench\cpu_sampler.py; psutil plus typeperf). Every 10 s record CPU by role (ffmpeg/ffprobe, chrome, 3D renderer, bridge python, Pocket, other), \Memory\Page Reads/sec, per-process hard faults and working set, free RAM, pagefile use, NIC bytes sent and C: free. Join with run folders and queue logs (path in C:\Users\meteh\Kanallar\Engineered\tools\queue_films.py) to compute accepted shots per hour, machine-seconds per accepted shot, solo wall-minutes per film-minute, and calls and tokens per film per lane (tokens 'n/a' where absent). Validate on EP04 (flash 884, codex 409, flash_review 87, gdirect 17). Overhead must stay below 1% CPU and 100 MB RAM. Run 30 min, then start a 24-h run in the background. Budget: 90 min.

#### Q2. Disk and in-flight report
- **Why:**
  - C: fills in 15 h at 40/day and in 2.5 days at 10/day: 5.4 GB per film, EP03 alone 7.64 GB in flight, 135.9 GB free. No tool shows this.
  - **Gain:** an input for the admission rule (C: reserve) and the baseline for A3.
- **Files:** TB\disk_report\ (new).
- **Depends on:** –. **Group:** W0-1. **Size/model:** S / haiku. **Flags:** –
- **Test:** one run on the current state. Totals must match `du -s` within 1% on three folders.
- **Accept:**
  - Per film: run-folder size split by top-level subfolder, ZIP size and delivered copy size.
  - Overall: yt_cache size, C: free, and growth since the previous run.
  - JSON plus a one-screen table, in under 60 s, read-only.
- **Risk / rollback:** read-only; none.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Write read-only C:\Users\meteh\testbench\disk_report\disk_report.py. Find run folders via C:\Users\meteh\Kanallar\Engineered\tools\queue_films.py, the delivery root via DELIVERY_ROOT in C:\Users\meteh\.gemini\scripts\documentary_materials\delivery.py (env DOCUMENTARY_DELIVERY_ROOT), and the yt_cache folder via yt_cache.py in the same package. For each film report: run-folder size split by top-level subfolder, ZIP size, and delivered copy size. Also report yt_cache total, C: free, and growth since the previous run (keep a small state JSON beside the script). Output JSON plus a one-screen text table. Check totals against du -s within 1% on three folders. It must finish in under 60 s and never delete or move anything. Budget: 40 min. Return the table for today's nine films.

#### Q3. drive.py and queue_films.py: honest exit codes, no instant retries
- **Why:** Ops gaps 4, 6, 7 and 8, and forgotten A2 and A3.
  - drive.py catches only HTTPError (:36-40).
  - reaudit (:13-28) has a 1,800-s timeout, sends its output to DEVNULL, and does not catch TimeoutExpired.
  - Stage-1 failures print nothing useful.
  - A duplicate EP02 launch was logged as "exit 3".
  - queue_films retries codes 3 and 4 at once, up to 3 times: EP05 burned all 3 retries in 40 s.
  - **Gain:** every failure line in the logs carries a class; 0 retries of duplicate jobs; transport errors are retried after 5 min instead of at once.
- **Files:** ENG\tools\drive.py, ENG\tools\queue_films.py, TB\drive_stub\ (new).
- **Depends on:** Q9. **Group:** W0-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:**
  - A stub server with one run per case: timeout, connection reset, non-JSON body, 500 carrying the allocation text, the duplicate-job text, a stage-1 FAIL with audit, and success.
  - Then one DIFF_MINI stage-2 run through `DRIVE_BRIDGE_URL=http://127.0.0.1:8199/run`.
- **Accept:**
  - Exit codes: 0 and 1–4 unchanged; 10 transport; 11 duplicate job; 12 reaudit timeout.
  - Every failure logs one `REASON` line.
  - New queue_films mapping:
    - 10: retry after 5 min, at most 3 times;
    - 11: never relaunch;
    - 12: FAILED;
    - 3 and 4: wait 10 min before each retry.
  - The success path is unchanged.
- **Risk / rollback:**
  - Running films keep the old drive.py; deploy by rename.
  - queue_films changes apply at its next start; never restart it mid-batch.
  - Rollback: git revert in the Kanallar repo (Q9).
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Harden C:\Users\meteh\Kanallar\Engineered\tools\drive.py and queue_films.py in the same folder. drive.py catches only HTTPError (:36-40), runs reaudit (:13-28) with a 1800 s timeout and output to DEVNULL without catching TimeoutExpired, and hard-codes the bridge URL. Add env DRIVE_BRIDGE_URL (default unchanged). New exit codes: 10 transport (URLError, reset, non-JSON); 11 'already has an active production job'; 12 reaudit timeout. Keep 0 and 1–4. On every failure write one log line 'REASON <class> <text>', including the stage-1 verdict and failing checks. Send reaudit output to stdout and log a heartbeat every 300 s. In queue_films.py: 10 retries after 5 min (max 3); 11 never relaunches; 12 means FAILED; 3 and 4 wait 10 min before each retry. Fix the docstring's RAM rule (code uses 1.5/2.5 GB). Test with a stub server in new C:\Users\meteh\testbench\drive_stub\, then one DIFF_MINI stage-2 run against :8199. Budget: 75 min.

#### Q4. run_when_free2.sh: one admission at a time
- **Why:** Ops gap 5 and forgotten A1.
  - `run_when_free.sh` uses `-le 4`, so it admits a fifth film.
  - Four pollers wake in lockstep every 60 s, and Git Bash fork stubs make processes look duplicated.
  - EP07 and EP09 started in the same second (14:57:15).
  - **Gain:** no herd starts, and at most 4 films in flight until the ledger (A4) replaces this script.
- **Files:** ENG\tools\run_when_free2.sh (new). The old file stays untouched.
- **Depends on:** Q9. **Group:** W0-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:**
  - Simulation with a fake drive.py that sleeps 120–600 s and a fake free-RAM value from env: 4 pollers × 30 cycles.
  - A killed lock holder, to test stale-lock recovery.
- **Accept:**
  - Never more than 4 films running at once.
  - Never two admissions less than 90 s apart.
  - A stale lock is recovered when its PID is dead or after 15 min.
  - Films are counted as unique folders, and the free-RAM ≥4.0 GB rule is kept.
- **Risk / rollback:** only new launches use the new script. Rollback: keep using the old file.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Do not edit C:\Users\meteh\Kanallar\Engineered\tools\run_when_free.sh: running copies read it incrementally. Write a new run_when_free2.sh in the same folder that takes the same arguments. Admission lock: mkdir C:\Users\meteh\Kanallar\Engineered\tools\.admit_lock, holding PID and time; it goes stale when the PID dies or after 15 min. Count in-flight films as unique film folders taken from drive.py command lines (Git Bash fork stubs duplicate processes), and admit only while the count is below 4. Keep the free RAM ≥4.0 GB rule. After an admission, hold the lock 90 s so the film's RAM shows. Poll with 45–75 s random jitter instead of a fixed 60 s. Test by simulation: a fake drive.py that sleeps, a fake RAM value via env, 4 pollers × 30 cycles, plus a killed lock holder. Budget: 60 min. Return the simulation summary.

#### Q5. supervisor.py: sees every film, stays alive
- **Why:** Ops gap 9, forgotten A4 and token gap G1.
  - `driving()` (:33) misparses its arguments.
  - :25 reads blackout_retry.log, which does not exist.
  - A regex at :82 never matches.
  - It never saw EP07, EP08, EP09 or EP10, which were started from stage 2 or 4.
  - It exits after every incident (:162-185), so Claude must re-arm it each time.
  - For unknown cases it asks codex and then Flash, 180 s each (:145-159).
  - Notification wake-ups cost 4.99M weighted tokens per day.
  - **Gain:** every stall and failure is seen, with no re-arm wake-ups.
- **Files:** ENG\tools\supervisor.py.
- **Depends on:** Q9; uses Q3's exit codes when present. **Group:** W0-1. **Size/model:** M / sonnet. **Flags:** –
- **Test:**
  - Offline replay of the 2026-10-30 logs: queue logs, batch.log, and each run folder's events.jsonl.
  - Then 2 h live beside production.
- **Accept:**
  - The replay flags EP07, EP08, EP09, EP10 and the EP05 retry burst, each within 10 min of its log time, and raises no alarm for EP04.
  - 0 LLM calls for known classes.
  - Live: no exit in 2 h, and at most 1 incident file per incident.
- **Risk / rollback:** a quieter supervisor could miss failures; the replay test is the guard. Rollback: git revert, or `supervisor.py.bak-stall`.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Fix C:\Users\meteh\Kanallar\Engineered\tools\supervisor.py. Known defects: driving() (:33) misparses drive.py arguments (parse by position); :25 reads blackout_retry.log, which does not exist (drop it); the :82 regex never matches; films started from stage 2 or 4 are invisible; it exits after each incident (:162-185); unknown cases ask codex, then Flash, 180 s each (:145-159). Make it long-lived. Liveness means film lock bytes plus the events.jsonl mtime in the run folder. Read the queue logs (path from queue_films.py in the same folder) and the drive.py exit codes 0–4, 10, 11 and 12. Write one incident file (class and evidence) per incident and keep running; call an LLM only for unclassified cases. Add --replay <dir> --clock <time> and replay the 2026-10-30 logs: EP07, EP08, EP09, EP10 and the EP05 retry burst must be flagged within 10 min, and EP04 must not be. Budget: 120 min.

#### Q6. SearXNG: honest health check, no crash
- **Why:** Ops gap 3, forgotten A6, and the user's request recorded in DURUM.md at 14:25.
  - `up()` (sources.py:860) probes `/search?q=test`.
    - The probe passed from about 11:26 to 14:45 while the image engines were dead: brave.images crashed and duckduckgo timed out.
    - EP07 and EP08 therefore got 0 archive photos.
  - At :873, `docker start searxng` runs with `timeout=60` and no try block. It crashed EP06 although the container was already up.
  - **Gain:** 0 stage-3 crashes caused by search, and a recorded `search_health` that A2 and A4 use.
- **Files:** DM\sources.py (ensure_searxng :850-882 and searxng_images :884-915 only), DM\tests\test_searxng_health.py (new).
- **Depends on:** –. **Group:** W0-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:**
  - Unit tests:
    - a dead port, via `DOCUMENTARY_SEARXNG=http://127.0.0.1:1`;
    - no docker on PATH;
    - a hanging docker stub.
  - Live: an image query returns at least 10 results within 8 s.
  - DIFF_MINI ×2 on :8199, compared with the wave baseline using plan_diff.
- **Accept:**
  - No exception escapes ensure_searxng.
  - `docker inspect` runs before `docker start`.
  - The service counts as healthy only when an image query returns ≥10 results within 8 s.
  - Dead is distinguished from slow, and the result is written as a `search_health` event.
  - plan_diff shows no change on DIFF_MINI.
- **Risk / rollback:** the stricter check reports status only; it does not fail the stage (A2 decides). Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In C:\Users\meteh\.gemini\scripts\documentary_materials\sources.py change only ensure_searxng (:850), its helper up() (:860), and searxng_images (:884) if needed. Today up() probes /search?q=test, which kept passing while the image engines were dead (11:26–14:45 on 2026-10-30). At :873, docker start runs with timeout=60 and no try block; it crashed a film while the container was already running. Define health as a categories=images query returning at least 10 results within 8 s. Run docker inspect before docker start. Catch TimeoutExpired, FileNotFoundError and OSError, tell dead apart from slow, and write a search_health event to the run folder. ensure_searxng must never raise, and must not fail the stage. Add unit tests: a dead port via DOCUMENTARY_SEARXNG, no docker on PATH, and a hanging docker stub. Then run DIFF_MINI ×2 on :8199 with plan_diff against the wave baseline. Budget: 75 min.

#### Q7. Bridge hardening [NEEDS_USER, NEEDS_IDLE]
- **Why:** Ops gaps 2, 7 and 11, and forgotten D.
  - `except Exception: pass` swallows reload errors at bridge :92-93, :120-121, :199-200 and :211-212, so a broken module silently runs old code.
  - Stage-1 FAIL bodies carry `error_type: null`.
  - Allocation failures return the same HTTP 500 as crashes.
  - The live bridge (PID 24956) has not logged since 11:02.
  - The bridge binds 0.0.0.0 (:30), and Dify calls it at `host.docker.internal:8099` (`update_dify_4stages.py:50/94/138`).
  - **Gain:** a failed reload becomes visible instead of silently running stale code, and every failure body can be classified.
- **Files:** SCR\documentary_native_bridge.py.
- **Depends on:** –, plus decision D8 for the bind address. **Group:** W0-idle. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D8: keep 0.0.0.0 for Dify and add a firewall rule, or bind 127.0.0.1), NEEDS_IDLE (restart).
- **Test:** on :8199:
  - a planted syntax error in a module copy gives 503 `reload_failed` naming the module, and restoring the module gives 200;
  - allocation and unresolved-shot failures return `error_class` and the shot ids;
  - a stage-1 FAIL carries its verdict and failing checks.
- **Accept:**
  - The test passes, and reload tracebacks are logged.
  - `DOCUMENTARY_BRIDGE_HOST` defaults to today's value.
  - The production restart happens in a drain window, with logs going to a known rotating file.
- **Risk / rollback:** a 503 is returned only for modules the requested stage imports. Rollback: git revert plus a restart.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Edit C:\Users\meteh\.gemini\scripts\documentary_native_bridge.py; test on its copy in C:\Users\meteh\testbench\scripts through :8199. (1) Replace the silent 'except Exception: pass' blocks at :92-93, :120-121, :199-200 and :211-212 with logged tracebacks. If a module the requested stage needs failed to reload, answer 503 {status: FAIL, error_class: reload_failed, module}. (2) Give stage failures an error_class (allocation_short, unresolved_shots, voice_text, code_bug) and the unresolved shot ids. A stage-1 FAIL must carry error_type, verdict and failing checks (:447-453). (3) Read HOST from env DOCUMENTARY_BRIDGE_HOST, keeping the default 0.0.0.0 (Dify calls host.docker.internal:8099). (4) Find where the live bridge's stdout and stderr go (silent since 11:02) and log to a rotating file. Restart production only in a drain window. Budget: 90 min.

#### Q8. Fix the empty-path crash in render.py:240
- **Why:** Forgotten A7. `_is_range_source` raised "WindowsPath('.') has an empty name" and crashed an EP02 shot render. **Gain:** this crash class goes to 0.
- **Files:** DM\render.py (`_is_range_source` and its render.py callers only), DM\tests\test_render_range_source.py (new).
- **Depends on:** –. **Group:** W0-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:**
  - Unit tests for None, `''`, `'.'`, a normal file and a range source.
  - One DIFF_MINI stage-3 pass on :8199.
- **Accept:** returns False for empty paths without raising and logs a warning with the shot id; other results are unchanged; the DIFF_MINI stage 3 completes.
- **Risk / rollback:** this could hide a caller bug, so the warning names the shot and a caller outside render.py is reported. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In C:\Users\meteh\.gemini\scripts\documentary_materials\render.py, _is_range_source (around :240) raised "WindowsPath('.') has an empty name" on 2026-10-30 and crashed a shot render in EP02. Make it return False for None, '' or '.' and log one warning with the shot id. Find which caller passes the empty path: fix it if it is in render.py, and report it if it is elsewhere (runner.py is owned by another item in this wave). Add C:\Users\meteh\.gemini\scripts\documentary_materials\tests\test_render_range_source.py covering None, '', '.', a normal file and a range source. Run one DIFF_MINI stage-3 pass on :8199. Budget: 45 min.

#### Q9. Local git for Kanallar, voice-lab and testbench
- **Why:**
  - Forgotten D: these three folders have no version control, and their backups are `.bak` files. They hold:
    - Kanallar: queue, drive, supervisor, preflight and SISTEM.md;
    - voice-lab: voice serving;
    - testbench: the bench.
  - Every Phase 0 item edits them.
  - **Gain:** changes become revertible and deploys diffable.
- **Files:** a new `.gitignore` and `.git` in each of the three folders.
- **Depends on:** –. **Group:** W0-0. **Size/model:** S / sonnet. **Flags:** –
- **Test:**
  - `git check-ignore` confirms that `ortak-site-anahtarlar.txt`, `*.log`, `queue/`, `incidents/` and `*.bak*` are ignored.
  - A key-pattern scan of the staged files, reporting counts only.
  - Repo size.
- **Accept:**
  - One initial commit per repo, containing only allowlisted files.
  - 0 key-pattern hits.
  - Nested repos are left out.
  - Each repo is under 50 MB.
- **Risk / rollback:** a secret or a large media file could be committed; the allowlist and the scan prevent that. Rollback: remove the new `.git` folder, a deletion that needs the user's approval.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Put three folders under local git, with no remote and no push: C:\Users\meteh\Kanallar, C:\Users\meteh\codex-repo-tests\voice-lab and C:\Users\meteh\testbench. First write a .gitignore in each. Kanallar ignores ortak-site-anahtarlar.txt, *.log, *.err, *.bak*, incidents/, queue/, supervisor_state.json, __pycache__/ and media files. voice-lab and testbench use allowlists: only *.py, *.ps1, *.sh, *.md and small config files; no models, audio, video, films or venvs. If a subfolder already has its own .git (check pocket-tts), leave it out. Before committing, scan the staged files for key patterns (AIza, sk-, ghp_, 'PRIVATE KEY') and report counts only; any hit blocks the commit. Never open or print key files. Keep each repo under 50 MB. Make one initial commit per repo only when the dispatcher allows. Budget: 45 min.

#### Q10. Hygiene inventory, listing only [NEEDS_USER, NEEDS_IDLE]
- **Why:** Forgotten D and G, and ops gap 17. The repo and testbench hold leftovers nobody has reviewed:
  - stray items in the production repo:
    - NUL, which holds 189 B of VDS host keys;
    - probe36.py;
    - GUN_RAPORU_2026-10-25.md;
  - 6 worktrees with 0 commits ahead (agent-a64cf9d holds .venv-bench and .scan_cache);
  - the refs tb/combo and candidate_tested, and branch a99137 compared with picture_fit.py (U13);
  - `.bak` files and empty items;
  - testbench experiments that reached no conclusion: gpu_pkg, batch_pkg, motion-prompt (930 files), profile_1030;
  - ctxmode project folders;
  - callers of `clean_video_watermark.py`.
  - **Gain:** the user decides on deletions in a single pass, and disk space comes back.
- **Files:** TB\hygiene\ (new).
- **Depends on:** –. **Group:** W0-2. **Size/model:** S / haiku. **Flags:** NEEDS_USER (deletions), NEEDS_IDLE (only the step that runs `DM\tests\test_media_memory.py` to settle U12).
- **Test:** spot-check 5 entries by hand.
- **Accept:** every item has its size, last-modified time, evidence of use and a proposed action; nothing is deleted or moved.
- **Risk / rollback:** read-only. NUL needs `\\?\` paths; never print its content.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Make a read-only inventory and delete nothing. Write C:\Users\meteh\testbench\hygiene\inventory.json and a short text table. In C:\Users\meteh\.gemini\scripts\documentary_materials cover: NUL (a reserved name, so use \\?\ paths and never print its content), probe36.py and GUN_RAPORU_2026-10-25.md; all git worktrees (commits ahead, size); refs tb/combo and candidate_tested; whether picture_fit.py supersedes branch a99137. Also cover: *.bak* and empty items under C:\Users\meteh\.gemini\scripts and C:\Users\meteh\Kanallar; the testbench experiment folders (gpu_pkg, batch_pkg, top3_pkg, nvenc_pkg, combo_pkg, cand_pkg, fastmotion, profile_1030, motion-prompt); ctxmode folders under C:\Users\meteh\.claude\projects; and callers of C:\Users\meteh\.gemini\scripts\clean_video_watermark.py. For each give size, last-modified time, evidence of use and a proposed action. Leave the :8433 server alone. Budget: 45 min.

#### Q11. Docs truth pass [NEEDS_USER]
- **Why:** Forgotten B and C, and token gap G9.
  - SISTEM.md has no lines for:
    - commits 6b33c20, 77861a3, 658c0f7, d947678 and 515cd22;
    - the drive reaudit, the supervisor `driving()` fix and seed_photos;
    - skill hiding, pyright off, and multiagents off.
  - Line 40 contains a literal TAB (`testbench<TAB>oken_audit`).
  - The 18.5-min best is attributed to Mayfield, but it was TOPIC_2, a 3:52 wildlife film.
  - Two different KEY.txt paths are named.
  - ENG\CLAUDE.md is stale.
  - **Gain:** every session starts from true facts.
- **Files:** `C:\Users\meteh\Kanallar\SISTEM.md`, ENG\CLAUDE.md.
- **Depends on:** Q9, and W0-1 merged. **Group:** W0-2. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (CLAUDE.md edit, which KEY.txt path, wording of the target re-base D1).
- **Test:** the user reviews the diff.
- **Accept:** the approved diff is applied, and SISTEM.md keeps its short format with newest entries first.
- **Risk / rollback:** wrong facts. Every line is checked against `git show` or a file. Rollback: git revert (Q9).
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Only with the user's approval of the diff, edit C:\Users\meteh\Kanallar\SISTEM.md and C:\Users\meteh\Kanallar\Engineered\CLAUDE.md. Show the diff first. In SISTEM.md, add one dated line each, newest first, for:
  - production commits 6b33c20, 77861a3, 658c0f7, d947678 and 515cd22 (read them with git show in C:\Users\meteh\.gemini\scripts\documentary_materials);
  - the drive.py reaudit path, the supervisor driving() fix, seed_photos.py, skill hiding, pyright off and multiagents MCP off;
  - the Phase 0 items merged so far.

  Also in SISTEM.md: replace the literal TAB on line 40 so it reads testbench\token_audit; record that the 18.5-min best was TOPIC_2, a 3:52 wildlife film, not Mayfield; keep the one KEY.txt path the user names. Align CLAUDE.md commands with the current tools in C:\Users\meteh\Kanallar\Engineered\tools. Budget: 40 min.

#### Q12. gemini_keys: a per-minute 429 does not mean "spent" [NEEDS_USER]
- **Why:** Forgotten A8. Any 429 marks a key spent (gemini_keys.py:120-121). On 2026-10-30, 23 of 46 key×model pairs were marked spent and only about 46 calls succeeded. A per-minute limit should only cool the key down. **Gain:** more burst capacity on the backup lane, still not counted as capacity.
- **Files:** DM\gemini_keys.py, DM\tests\test_gemini_keys_429.py (new).
- **Depends on:** –. **Group:** W0-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D4: keep the free-tier lane at all).
- **Test:**
  - Replay the saved 429 bodies (from `TB\gem_probe.py`, or capture one of each kind) through `report()`.
  - Unit tests per quota kind.
  - 8 of 8 testbench calls OK.
- **Accept:**
  - A per-minute 429 gives a 60-s cooldown.
  - A per-day or unknown 429 marks the key spent, as today.
  - After 3 cooldowns in an hour, the key counts as spent.
  - Keys appear only by their last 4 characters.
- **Risk / rollback:** a daily 429 misread as per-minute would cause repeated 429s; the 3-cooldown cap limits that. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Proceed only after the user confirms the free-tier key lane stays (D4). In C:\Users\meteh\.gemini\scripts\documentary_materials\gemini_keys.py, report() (:114) marks a key spent on any 429 (:120-121). Parse the 429 body's quota details (quotaId or violations; per minute or per day). Per-minute: cool down 60 s. Per-day: mark spent, as today. Unknown: spent. After 3 cooldowns in an hour, a key counts as spent. Keep %LOCALAPPDATA%\documentary_materials\gemini_usage.json compatible. Identify keys only by their last four characters; never print, log or copy a key. Use bodies saved by C:\Users\meteh\testbench\gem_probe.py, or capture one 429 of each kind. Add C:\Users\meteh\.gemini\scripts\documentary_materials\tests\test_gemini_keys_429.py, then run 8 calls through the lane on the testbench. Budget: 60 min.

#### Q13. Stop requesting logo removal [NEEDS_USER]
- **Why:**
  - Forgotten F, and the standing rule against removing watermarks or logos.
  - The `remove_logo` option is sent to G-Labs at anim.py:375, runner.py:1743 and `SkullStudio\pipeline\gen2.py:73`.
  - **Gain:** compliance with the rule, with the ANIM pass rate measured to stay within run-to-run spread.
- **Files:** DM\anim.py, DM\runner.py (:1743 only), `C:\Users\meteh\SkullStudio\pipeline\gen2.py` (:73 only).
- **Depends on:** decision D5. **Group:** W0-2. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D5; SkullStudio belongs to the other line).
- **Test:**
  - Generate 5 ANIM assets on the testbench without the flag and check them for marks.
  - Run DIFF_MINI ×2 per side and compare ANIM pass rates.
- **Accept:**
  - No call sends `remove_logo`.
  - ANIM pass rate stays within spread.
  - Any marks found are reported as a supply problem.
- **Risk / rollback:** assets that carry marks get rejected in review. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. With the user's approval (D5), stop sending the remove_logo option to G-Labs at C:\Users\meteh\.gemini\scripts\documentary_materials\anim.py:375, runner.py:1743 in the same folder, and C:\Users\meteh\SkullStudio\pipeline\gen2.py:73. Change nothing else in those files. Generate 5 ANIM assets through the testbench (:8199) without the flag. Check each for logos or watermarks with one Flash vision prompt per image, then show them to the dispatcher. Run DIFF_MINI ×2 and compare the ANIM pass rate with the wave baseline. Never add any logo or watermark removal step; if marks appear, report it as a supply problem. Budget: 60 min.

#### Q14. Pocket priority and recycle-limit A/B [NEEDS_IDLE]
- **Why:**
  - Pocket runs at 2.83x realtime alone but at 0.19x under contention.
  - On 2026-10-30 the process held 3,033 MB private memory with a 2 MB working set, so it was paged out.
  - At 20 films/day and 0.19x, voice needs 104% of the day.
  - **Gain target:** at least 20% higher realtime factor under load, with identical audio.
- **Files:** TB\pocket_ab\ (new): a copy of `VL\pocket-tts\pocket_serve.py` run on :7873, plus a load generator.
- **Depends on:** –. **Group:** W0-idle. **Size/model:** S/M / sonnet. **Flags:** NEEDS_IDLE (synthetic load, plus 3 GB for a second Pocket).
- **Test:**
  - Four arms: Normal or AboveNormal priority × RECYCLE_MB 3500 or 2500.
  - At least 3 runs per arm of a fixed 60-sentence text, under a load of 4 ffmpeg encodes.
  - Measure realtime factor, hard faults, working set, and audio identity.
- **Accept:**
  - A recommended arm with realtime factor ≥1.2× the Normal/3500 arm.
  - Identical audio bytes for the same seed; if bytes differ, ECAPA ≥0.99 against Normal/3500.
- **Risk / rollback:** none for production; this is a copy on another port. Never use Realtime priority.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Run only in a drain window. Copy C:\Users\meteh\codex-repo-tests\voice-lab\pocket-tts\pocket_serve.py into new C:\Users\meteh\testbench\pocket_ab\ and run it on port 7873 with the same model and voice. Read C:\Users\meteh\codex-repo-tests\voice-lab\Start-Pocket.ps1, and do not touch the production Pocket on :7863. Arms: process priority Normal or AboveNormal (never Realtime) × RECYCLE_MB 3500 or 2500 (pocket_serve.py:64). For each arm run at least 3 syntheses of the same 60 sentences with the same seed, while 4 ffmpeg libx264 encodes load the CPU. Record realtime factor, hard page faults, working set, and whether the audio bytes match the Normal/3500 arm (otherwise ECAPA similarity). Stop the copy and the load afterwards. Budget: 90 min. Return a table per run and a recommended arm.

### Phase T: Claude token economy

Baseline for every T item: 34.5M weighted tokens (wM) per day over 2,058 calls on 2026-10-30; the commander session takes 73%; notification wake-ups 4.99M wM/day; a main call costs about 19.6k wM (Arch §2.9). Weights: input 1, 1-h cache write 2.0, cache read 0.1, output 5, Opus = 1, Sonnet = 0.6, Haiku = 0.2. T1 is merged into Q5 and T12 has no brief. T items use headless probes (`claude -p --output-format json` in a neutral folder) and the scripts in `TB\token_audit\gh1030`. None may change the main model, the 1-h cache TTL (kept: 5 min would add 63% cost) or `autoCompactWindow` 200000 (kept: at the measured optimum).

#### T2. Batch runbook for the commander session
- **Why:** The commander rediscovers the batch procedure (preflight, queue, status, who to wake) in every session, and each rediscovery costs main-call tokens.
- **Files:** ENG\RUNBOOK_BATCH.md (new). ENG\CLAUDE.md is Q11's and stays untouched.
- **Depends on:** –. **Group:** WT-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:** three replayed incidents (EP05 retry burst, EP07 allocation failure, EP02 3D visual_fit loop) given to a headless session in ENG, 2 runs with the runbook and 2 without. Every command in the runbook is executed once with `--help` or a dry run.
- **Accept:** at most 120 lines; one action per error class of Arch §4.4; with the runbook the 3 incidents cost at least 30% fewer weighted tokens, and the answers are correct in all runs.
- **Risk / rollback:** a stale command misleads the commander, so each command is checked against the file on disk. Rollback: delete the file.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Write C:\Users\meteh\Kanallar\Engineered\RUNBOOK_BATCH.md for the commander session. Sections: start of batch (preflight.py, queue_films.py, run_when_free2.sh when it exists); how to read state (queue logs, status.json if present, events.jsonl); one action per error class from Arch §4.4; what is never done by hand (yt_gate, slot limits, judges); when to wake the user. Link to files, do not paste their content. Verify every command and path exists. Then run the 3 replayed incidents with and without the file through `claude -p --output-format json` (2 runs each) and report weighted tokens and correctness per run. Budget: 45 min.

#### T3. Role agent files [NEEDS_USER]
- **Why:** Sub-agents are 22% of weekly weighted tokens (2,465 Opus sub calls at mean context 164k). A role file with a narrow tool list and a fixed model makes the model choice and the prefix size explicit instead of left to each brief.
- **Files:** `C:\Users\meteh\.claude\agents\` (new): scan (haiku, read-only tools), coder (sonnet), architect (opus, read-only).
- **Depends on:** –; T5 and T7 numbers help but are not required. **Group:** WT-user-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D15; the exact files are approved before they are written).
- **Test:** the same 3 standard tasks (a file scan, a small code fix with a test, a design question) on each role file and on `general-purpose`, 2 runs each, headless, with the model forced by `CLAUDE_CODE_SUBAGENT_MODEL` unset for the comparison.
- **Accept:** first-call prefix of scan and coder at least 25% below `general-purpose` (target, measured per agent); result quality equal on all 3 tasks; weighted tokens per task reported.
- **Risk / rollback:** a role file with too few tools stalls a task; each file lists its tools in the diff. Rollback: delete the files.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Draft three agent files for C:\Users\meteh\.claude\agents\ but show the diff to the dispatcher before writing: scan (model haiku; Read, Grep, Glob, read-only Bash), coder (model sonnet; Read, Edit, Write, Bash, Grep, Glob; follows WORKPLAN §1), architect (model opus; read-only; returns decisions, not code dumps). Each file states the return limit (at most 15 lines). After approval, measure the first-call token count and weighted cost of each role against `general-purpose` on the 3 standard tasks (2 runs each, headless). Do not edit settings.json or CLAUDE.md. Budget: 60 min.

#### T4. Workflow scripts for batches
- **Why:** Dispatching a wave by hand costs one commander call per agent start, per return and per check. One Workflow per wave moves that into the script, with explicit models per step.
- **Files:** `C:\Users\meteh\Kanallar\workflows\` (new): wave dispatch, canary-and-diff, batch status.
- **Depends on:** –. **Group:** WT-1. **Size/model:** M / sonnet. **Flags:** –
- **Test:** dry-run the wave dispatch with two stub items (no production calls), then one real canary-and-diff on DIFF_MINI ×2 against :8199. Count commander calls and weighted tokens for the same work done by hand.
- **Accept:** commander calls per wave at most one third of the manual count; every step names its model; Haiku for scans, Sonnet for code, Opus only for judgement; scripts take paths, not pasted text.
- **Risk / rollback:** a script that restarts a shared service by itself. None may; shared restarts stay behind NEEDS_IDLE. Rollback: delete the folder.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md and load the workflow-authoring skill. In new C:\Users\meteh\Kanallar\workflows\ write three Workflow scripts. (1) wave_dispatch: takes a wave ID, reads §3, starts one agent per item with the item's brief verbatim, checks the file-ownership rule, collects the returns (at most 15 lines each) into one file. (2) canary_diff: runs DIFF_MINI twice per side on :8199 and calls diff_films.py and plan_diff.py. (3) batch_status: reads status.json or the queue logs and writes one summary. Explicit models per step. Test with stub items first, then one real canary. Report commander calls and weighted tokens against doing it by hand. Budget: 90 min.

#### T5. Sub-agent brief A/B
- **Why:** The brief is the only context a sub-agent has. Whether inline context, path references or a terse brief costs fewer tokens at equal success is unmeasured (Arch §11, U17).
- **Files:** TB\token_audit\brief_ab\ (new).
- **Depends on:** –. **Group:** WT-1. **Size/model:** M / sonnet. **Flags:** –
- **Test:** 3 tasks × 3 brief shapes (inline context, path references as in this plan, terse) × 3 runs, headless with Sonnet. A fixed checker scores each result pass or fail.
- **Accept:** a table of weighted tokens, tool calls and pass rate per shape with every run listed; a recommendation only if one shape is at least 20% cheaper at the same pass rate, otherwise "no difference".
- **Risk / rollback:** none; read-only apart from the new folder.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In new C:\Users\meteh\testbench\token_audit\brief_ab\ build an A/B harness around `claude -p --output-format json` (reuse C:\Users\meteh\testbench\token_audit\gh1030\usage_map.py for weights). Three small, checkable tasks from this repo (find where X is set; fix a failing unit test; explain a function in at most 5 lines). Three brief shapes per task: A inline context, B file-path references plus the §1 rules, C terse goal only. Three runs per cell, Sonnet, neutral working folder copy. Score with a script, not by eye. Report all 27 runs. Do not change any settings. Budget: 75 min.

#### T6. Wrap-up and return-format A/B
- **Why:** Every sub-agent return enters the commander's context, and the commander's context is re-read on every later call (cache read 0.1 per token). A shorter return that keeps the decision facts saves weight on all later calls.
- **Files:** TB\token_audit\wrapup\ (new).
- **Depends on:** –. **Group:** WT-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:** take 10 real sub-agent returns from the 2026-10-30 transcripts; re-produce each in 3 formats (current free text, the 15-line §1 format, a result file plus a 3-line pointer); a headless commander answers the same 3 follow-up decisions from each.
- **Accept:** decision accuracy equal across formats; tokens added to the commander per return at least 30% lower than free text for the recommended format; all 30 answers listed.
- **Risk / rollback:** none; read-only.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In new C:\Users\meteh\testbench\token_audit\wrapup\ measure return formats. Pick 10 real sub-agent returns from the transcripts under C:\Users\meteh\.claude\projects\C--Users-meteh--gemini-scripts-documentary-materials (use a Haiku scan to list them; pass paths). Rewrite each in three formats: as it was, the §1 item 15 format, and a file with a 3-line pointer. For each format a headless Sonnet commander answers the same three follow-up decision questions per return; score against the original facts. Report tokens added to the commander per return and decision accuracy per format. Budget: 60 min.

#### T7. Tool and skill load measurement
- **Why:** The 2026-10-30 probe found per-call prefix savings of 3,780 tokens (skills name-only, applied), 1,909 (strict MCP, applied), 626 (skill description length) and 460 (git instructions), but not what each remaining tool, skill and MCP server costs. Prefix cuts are small in weight (about 0.7% of an Opus call), so only measured items count.
- **Files:** TB\token_audit\tools_load\ (new).
- **Depends on:** –. **Group:** WT-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:** headless probes in a neutral folder with one component removed at a time (`--settings` overlays, `--strict-mcp-config`, `--disallowedTools`), 2 runs each.
- **Accept:** a ranked table of prefix tokens per component, with weekly weighted saving = tokens × 0.1 × the 6,035 weekly Opus main calls; items below 0.5% of weekly Opus main are marked "skip"; T9 gets the list.
- **Risk / rollback:** none; overlays are per-run and change no settings file.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Read C:\Users\meteh\testbench\token_audit\RESULTS_1030.md and the scripts in the gh1030 folder beside it. In new C:\Users\meteh\testbench\token_audit\tools_load\ measure the first-call prefix with each of these removed alone: each deferred tool group, each MCP server, each remaining listed skill (update-config, code-review, simplify, loop, workflow-authoring, run, youtube-production-audit), the memory index. Use `claude -p --output-format json` from a neutral folder and `--settings` overlays only; never edit a settings file. Two runs per overlay. Output the ranked table and the weekly saving per item. Budget: 60 min.

#### T8. wait_film.py: one blocking wait instead of wake-ups
- **Why:** Notification wake-ups cost 4.99M wM/day (14.5% of 34.5M) and each main call costs about 19.6k wM whatever its result size. A command that blocks until something needs Claude replaces many wake-ups with one call.
- **Files:** ENG\tools\wait_film.py (new).
- **Depends on:** –; uses Q3 exit codes and the Q5 `--replay` option when present. **Group:** WT-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:** replay of the 2026-10-30 queue logs (with a fake clock), then one live DIFF_MINI stage-2 run against :8199, and a missing-status.json case.
- **Accept:** prints exactly one line (film, stage, class, next action) and exits on the first terminal state, an incident of class unknown or code_bug, or a 30-min heartbeat; 0 LLM calls; polling below 0.1% CPU; documented exit codes.
- **Risk / rollback:** a waiter that never wakes Claude hides a stall, so the heartbeat is mandatory. Rollback: delete the file.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Write C:\Users\meteh\Kanallar\Engineered\tools\wait_film.py: `wait_film.py <film|all> [--until done|incident|any] [--heartbeat 1800] [--replay DIR --clock T]`. It polls only files (queue logs from queue_films.py, run-folder events.jsonl and lock bytes, status.json when it exists), never the network, and never calls an LLM. Known failure classes are printed and the wait continues; it exits on done, on unknown or code_bug incidents, or on the heartbeat. One output line, fixed exit codes. Test on the 2026-10-30 logs and one live DIFF_MINI run on :8199. Budget: 60 min.

#### T9. settings.json cleanup [NEEDS_USER]
- **Why:** Apply only the measured prefix and diagnostics savings from T7 (already applied: skills name-only, pyright off, multiagents MCP off).
- **Files:** `C:\Users\meteh\.claude\settings.json`.
- **Depends on:** T7. **Group:** WT-user-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D15; the exact diff).
- **Test:** headless prefix probe before and after (2 runs each); one ordinary session still starts with hooks and plugins working.
- **Accept:** prefix reduced by the measured sum of the approved items; no change to the model, effort, `autoCompactWindow` 200000 or the 1-h cache TTL; backup `settings.json.bak-T9` exists.
- **Risk / rollback:** a hidden skill or plugin that a channel session needs. Rollback: restore the backup.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Take the T7 table and propose a settings.json diff with only the items at or above 0.5% of weekly Opus main weight. Candidates already measured: skillListingMaxDescChars 200 (-626 tokens per call), includeGitInstructions false (-460). Rejected earlier, do not retry: disableBundledSkills (+5,200), bashOutputMaxChars, a 5-minute cache TTL, a lower autoCompactWindow. Show the diff to the dispatcher and wait for approval (rule 9). Make the backup first, apply, then re-run the headless prefix probe. Budget: 30 min.

#### T10. durum.py hook: bounded injection [NEEDS_USER]
- **Why:** The SessionStart hook puts DURUM.md back into context after startup, clear and compaction. Whatever it injects is re-read on every later call, so its size and staleness matter, and the chars-per-token estimate is approximate (Arch §11, U17).
- **Files:** `C:\Users\meteh\.claude\hooks\durum.py`.
- **Depends on:** –. **Group:** WT-user-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D15; hook change).
- **Test:** headless sessions in documentary_materials on startup, clear and compact; count injected tokens from the first call's usage; a DURUM.md of 200 lines as the stress case.
- **Accept:** injected text capped at 1,500 tokens with a visible "truncated, N lines omitted" line; sections older than 7 days are flagged, not deleted; the file is still injected after /compact; all three events tested.
- **Risk / rollback:** a cap that drops a live section. Truncation keeps the newest sections first. Rollback: restore `durum.py.bak-T10`.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Read C:\Users\meteh\.claude\hooks\durum.py and C:\Users\meteh\.gemini\scripts\documentary_materials\.claude\DURUM.md. Propose a diff that caps the injected text at 1,500 tokens (calibrate chars per token by one measured probe, not by guess), keeps the newest sections, flags sections older than 7 days, and prints how many lines were omitted. Show the diff and wait for approval before editing. Back up first. Test startup, clear and compact in headless sessions and report injected tokens before and after. Budget: 40 min.

#### T11. rtk coverage for batch commands [NEEDS_USER]
- **Why:** rtk cut 86k tokens (36% of command output) on its first day over 1,114 commands, about 1% of total context. Batch work runs commands rtk may not cover (queue logs, drive output, ffmpeg and pytest logs).
- **Files:** `C:\Users\meteh\.claude\settings.json` (hook entries only).
- **Depends on:** T9 (same file). **Group:** WT-user-2. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D15; settings change).
- **Test:** replay the Bash outputs of the last 7 days through rtk offline and count tokens before and after, by command family; check that no output needed for a decision was cut (10 sampled cases by hand).
- **Accept:** a list of command families where the cut is at least 30% with no lost decision fact; the diff adds only those; the measured weekly saving is reported, and "no change" is a valid result.
- **Risk / rollback:** a filter hides an error line. Rollback: restore the T9 backup.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Wait for T9 to be merged. Using the Bash tool outputs in the 7-day transcripts (Haiku scan, paths only), group commands by family and run each through rtk offline. Report tokens before and after per family and check 10 sampled outputs by hand for lost error lines. Propose a settings.json diff for families with a cut of at least 30% and no loss; show it and wait for approval. Do not touch other settings. Budget: 60 min.

#### T13. Memory consolidation [NEEDS_USER]
- **Why:** MEMORY.md is loaded into every session of the project, and some entries are stale (the 18.5-min best is attributed to Mayfield; the speed target is paused). Merging duplicates and fixing stale facts shrinks the prefix and removes wrong guidance.
- **Files:** the two memory folders under `C:\Users\meteh\.claude\projects\` that hold a `memory` directory for documentary_materials and Kanallar (list them first and name them to the dispatcher).
- **Depends on:** –. **Group:** WT-user-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D15; memory edits).
- **Test:** the user reviews a per-file diff; headless probe of the first-call prefix before and after.
- **Accept:** index at most 60% of today's size in tokens; every dropped fact is listed with its reason; nothing is deleted without the user's yes (merged files are kept as `.bak` until approved).
- **Risk / rollback:** a lost lesson. Rollback: restore the `.bak` files.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Only with the user's approval of the diff. List the project memory folders under C:\Users\meteh\.claude\projects, read MEMORY.md and each linked file (Haiku scan allowed, return paths and sizes), and propose merges of duplicates, corrections of stale facts (check each against the repo or SISTEM.md), and a shorter index. Write nothing until the dispatcher approves the exact diff. Then apply with `.bak` copies and report the prefix size before and after. Budget: 45 min.

#### T14. Claude tokens per delivered film
- **Why:** The Phase T exit (down at least 40% per delivered film against 2026-10-30) has no number yet. 2026-10-30 delivered 1 film at 34.5M wM, so the day figure is the baseline, not a rate.
- **Files:** TB\token_audit\per_film\ (new).
- **Depends on:** –. **Group:** WT-1. **Size/model:** M / sonnet. **Flags:** –
- **Test:** rebuild 2026-10-30 from the transcripts and compare with `usage_map.py` and the 34.5M / 2,058 figures.
- **Accept:** the rebuilt day total is within ±2% of `usage_map.py`; the daily report gives weighted tokens by commander, sub-agent and workflow, wake-up count, and weighted tokens per delivered film (films from the queue logs, later the ledger).
- **Risk / rollback:** read-only; delete the folder.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Build on C:\Users\meteh\testbench\token_audit\gh1030\usage_map.py. In new C:\Users\meteh\testbench\token_audit\per_film\ write a daily report: weighted tokens by kind (main, sub, workflow) and model family, notification wake-ups (see notif.py in gh1030), and tokens per delivered film, with delivered films taken from the queue logs of ENG\tools\queue_films.py. Validate on 2026-10-30 against usage_map.py within ±2%. Write one JSON plus a one-screen table; run it for the last 7 days and store the baseline. Budget: 60 min.

### Phase A: a reliable 10 films/day

#### A1. State survives module reload [NEEDS_IDLE]
- **Why:** The governor is reset on every reload, so Flash peaked at 23 concurrent calls against a cap of 15 (Arch §2.7). Registries and the voice lock must survive too. **Gain:** Flash peak ≤15 (Phase A exit).
- **Files:** SCR\adaptive_governor.py, DM\resources.py, DM\runner.py, DM\io.py, DM\recovery.py, DM\three_render.py, DM\sources.py, DM\tests\test_reload_state.py (new).
- **Depends on:** Q6 merged (sources.py). **Group:** WA-1. **Size/model:** M / sonnet. **Flags:** NEEDS_IDLE (first bridge restart that loads the new pattern).
- **Test:**
  - Unit test: semaphores, counters, caches and the voice lock are the same object after two simulated reloads.
  - On :8199: 30 stub Flash calls spread across a reload.
  - DIFF_MINI ×2 with plan_diff.
- **Accept:** in-flight Flash never above the 15-slot cap across a reload; limits are re-read from the profile on reload, counts persist; U8 (which import re-registers the yt-dlp PoTokenProvider) resolved or reported; plan_diff shows no change.
- **Risk / rollback:** a persisted count that never drains blocks new calls, so counts are released in `finally`. Rollback: git revert, deployed in a drain window.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Move every module-level lock, semaphore, counter and cache in adaptive_governor.py, resources.py, io.py, recovery.py, three_render.py, sources.py and the runner registries onto the `globals().get(...)` pattern (see bbc_library.py:534). Slot limits keep coming from system_speed_profile.json on every reload; only counts persist. Release counts in `finally`. Find out which import re-registers yt-dlp's PoTokenProvider after a reload (U8) and keep it working. Write tests/test_reload_state.py. Test on :8199 with 30 stub Flash calls across a reload, then DIFF_MINI ×2. Do not restart production. Budget: 90 min.

#### A2. Feasibility gate and photo supply [NEEDS_USER]
- **Why:** Three films died with "No feasible narrative/category allocation" (EP05, EP07, EP08), mostly from an empty archive photo pool; EP05 had 41 photos and its cause is unknown (U5). **Gain:** 0 allocation crashes.
- **Files:** DM\sources.py, DM\planning.py, DM\runner.py, DM\photo_sources.py (new), DM\credits.py (new), new tests.
- **Depends on:** A1 and Q6 merged. **Group:** WA-2. **Size/model:** L / sonnet. **Flags:** NEEDS_USER (D2: licence allowlist and credit format).
- **Test:**
  - Feasibility gate on recorded EP05, EP07 and EP08 inputs: it raises `ALLOCATION_SHORT:<category>:<have>/<need>` before the MILP.
  - Each photo API on 5 queries.
  - DIFF_MINI ×2: plan_diff must show the category ratios unchanged.
- **Accept:** no HTTP 500 for a short category; a top-up of the short category runs once and the plan reruns; every non-YouTube asset has a credit line; U5 answered.
- **Risk / rollback:** a wrong licence. Only allowlisted sources are used. The planner keeps "ratios were not silently changed" (planning.py:1319). Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Proceed only after the user gives the licence allowlist (D2). (a) A feasibility check before the MILP in planning.py that counts usable assets per category and raises `ALLOCATION_SHORT:<category>:<have>/<need>`. (b) photo_sources.py for the allowlisted APIs (Wikimedia Commons, NASA Images, Library of Congress, Internet Archive, Openverse) and credits.py. (c) An in-process top-up using the seed_photos.py logic, once per category, then rerun planning. (d) Find why EP05 failed with 41 photos (U5) from its run folder. Use the search_health event from Q6. Never change ratios. Test on the recorded inputs, then DIFF_MINI ×2. Budget: 150 min.

#### A3. Retention, delivery staging and cache cap [NEEDS_USER]
- **Why:** C: takes 5.4 GB per film and fills in 2.5 days at 10/day; delivery.py:147 swallows a PermissionError caused by OneDrive sync. **Gain:** at most 0.3 GB per film left on C: after a verified delivery.
- **Files:** DM\delivery.py, DM\yt_cache.py, DM\retention.py (new), DM\tests\test_retention.py (new).
- **Depends on:** Q2 merged (baseline). **Group:** WA-1. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D3 and D12: delivery root per channel, retention period, what is kept, archive target).
- **Test:** on a copy of a finished film folder: staging, sha256 manifest, delivery, then retention in dry-run mode; a locked destination file; yt_cache cap with a fake 20 GB cache.
- **Accept:** delivery is built outside OneDrive and moved; the manifest verifies; retention keeps plan, EDL, report, voice master and credits; nothing is removed unless the sha256 verified (default dry-run); the yt_cache byte cap never touches `bucket.json`.
- **Risk / rollback:** data loss. Retention only lists unless the user switches deletion on; this item deletes nothing by default. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Use the policy the user approved (D3/D12). In delivery.py build the delivery in a staging folder outside OneDrive, write a sha256 manifest, move it, and stop swallowing the PermissionError at :147 (retry, then report). In new retention.py add a retention plan: dry-run listing by default, deletion only behind an explicit flag, and only after the delivered copy verifies. In yt_cache.py add an LRU byte cap that never touches bucket.json or pacing. Test on a copy, not on a live film. Never delete data yourself. Budget: 90 min.

#### A4. Ledger daemon in shadow mode [NEEDS_USER]
- **Why:** State lives in ad hoc queue logs and process tables; 27% of film-minutes were idle and about 14 runs were manual (Arch §4.3–§4.5). **Gain:** the classifier and admission decisions recorded for 48 h with at least 95% agreement before cutover.
- **Files:** ENG\ledger\ (new): films.db schema, classifier, admission, status.json writer, daily report.
- **Depends on:** Q3 and Q5 merged. **Group:** WA-1. **Size/model:** L / sonnet. **Flags:** NEEDS_USER (D7: cutover, retiring queue_films.py and run_when_free*.sh).
- **Test:**
  - Replay of the 2026-10-30 logs: every failure is classified per Arch §4.4.
  - Then 48 h in shadow beside production, recording the decisions it would have made.
- **Accept:** one writer; sqlite WAL; status.json updated every 20 s; admission checks per §4.5 (free RAM, C: reserve, services, inputs ready); shadow agreement ≥95% on admissions and classes; no change to production behaviour.
- **Risk / rollback:** shadow mode only reads. Cutover is a separate user decision.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md and Arch §4.3–§4.5. Build C:\Users\meteh\Kanallar\Engineered\ledger\: a stdlib sqlite3 WAL database with the five tables of §4.3, one writer daemon, a classifier for the §4.4 classes (read voice_audit.json for stage-1 FAILs, because error_type is null; read message text for allocation failures), the §4.5 admission rules, drain mode, status.json and a daily report. In shadow mode it only reads the queue logs and process table and writes the decisions it would make. Replay the 2026-10-30 logs, then run it 48 h beside production and report agreement. Do not start, stop or launch any film. Budget: 180 min.

#### A5. Fallback ladder and breakers [NEEDS_USER]
- **Why:** 3D shots fail 59–83% of the time; EP02 shots 61, 91 and 125 failed visual_fit on every attempt with identical review text; G-Labs went down at 11:33:53 and ANIM shots kept retrying. **Gain:** fewer wasted render seconds (30–46% of render and anim time went to shots that never passed).
- **Files:** DM\planning.py, DM\runner.py, DM\anim.py.
- **Depends on:** A2 merged. **Group:** WA-3. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D6: ladder order and ANIM share).
- **Test:** unit tests for the routing rules; replay EP02's three shots; a stub G-Labs that fails; DIFF_MINI ×2 and ×2 baseline, comparing wasted render seconds, PARTIAL count and the delivered mix.
- **Accept:** weather, radar, map and diagram beats never route to 3D; after 2 FAILs with the same review signature a shot moves VIDEO → PHOTO → CARD → MOTION; breaker state is saved per film; the G-Labs breaker opens and closes; wasted render seconds fall and the PARTIAL count is not above baseline; judges untouched.
- **Risk / rollback:** the ladder could change the mix, so the mix is reported per film. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Use the ladder order the user approved (D6). In planning.py keep weather, radar, map and diagram beats away from GENERATE_3D. In runner.py, compare the review signature (the failing check and the review text hash) of consecutive attempts; after two identical signatures move the shot one step down the ladder and record the route. Save breaker state per film so a rerun keeps it. In anim.py add a G-Labs breaker that opens after repeated "Max Retries Exceeded" and lets the film continue. Do not touch review prompts or thresholds. Test as listed, 2 runs per side. Budget: 120 min.

#### A6. Deep preflight, every 10 minutes
- **Why:** The 2026-10-30 health probes passed while SearXNG's image engines were dead for 3 hours. **Gain:** admission sees real service state.
- **Files:** `C:\Users\meteh\Kanallar\preflight.py`.
- **Depends on:** Q6 (uses the same image probe). **Group:** WA-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:** run against live services, then with each service stopped or stubbed dead in turn (Pocket, 9router, SearXNG, GPT gateway, G-Labs).
- **Accept:** each check tests real work (a Pocket sentence, a Flash call, a SearXNG image query with ≥10 results in 8 s, a GPT gateway call, a G-Labs status call), prints PASS, WARN or FAIL with a cause, and the whole run finishes in under 30 s; a `--loop 600` mode writes status.json for the ledger; the existing ~8 s mode still works.
- **Risk / rollback:** the checks spend a few LLM calls per cycle; they are counted and capped at 10 per cycle. Rollback: git revert (Q9).
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Extend C:\Users\meteh\Kanallar\preflight.py with deep checks that do real work for Pocket :7863 (one short sentence), 9router Flash, the GPT gateway, SearXNG (images, ≥10 results in 8 s; reuse the Q6 definition), G-Labs, PO token and the YouTube cookie. Add `--loop 600` that writes a status file the ledger can read. Keep the current fast mode and its output. Never print keys. Test each check by stopping or stubbing its service. Budget: 60 min.

#### A7. Service wrapper and restart plan [NEEDS_USER, NEEDS_IDLE]
- **Why:** Pocket, SearXNG, G-Labs and the bridge are started by hand; the live bridge's log has been silent since 11:02 (U6). **Gain:** a restart takes one command and leaves logs in a known place.
- **Files:** `C:\Users\meteh\Kanallar\services\` (new): PowerShell wrapper, one definition file per service.
- **Depends on:** –. **Group:** W0-idle. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D7: Task Scheduler registration), NEEDS_IDLE (a real restart test).
- **Test:** wrapper dry-run for each service; a real stop and start of a spare service copy (Pocket copy on another port) in a drain window.
- **Accept:** `status`, `start`, `stop` and `restart` per service; logs go to rotating files; start never touches a service that is already healthy; the Task Scheduler definition is written but not registered.
- **Risk / rollback:** a restart during a film. Drain mode first. Rollback: delete the folder.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In new C:\Users\meteh\Kanallar\services\ write a PowerShell wrapper (UTF-8 output, absolute paths) with status, start, stop and restart for Pocket (VL\Start-Pocket.ps1), SearXNG, G-Labs and the bridge. Each service has a definition file (command, port, health URL, log path). Logs rotate. Start does nothing when the health URL is already good. Find where the live bridge's stdout and stderr go (U6). Write a Task Scheduler XML but do not register it. Test only on spare copies in a drain window; never restart production services. Budget: 75 min.

#### A8. Voice step 2 and audit: time-outs, retries, fallback [NEEDS_USER]
- **Why:** 6 of 9 films failed stage 1 first time: 9router ReadTimeout on 5 of 6 audit segments (EP02), Gemini 503 (EP08). **Gain:** voice first-audit pass ≥60% (Phase A exit).
- **Files:** SCR\documentary_voice_step2.py, SCR\documentary_voice_audit.py, SCR\documentary_voice_audit_config.json, SCR\ask_frontier_models.py.
- **Depends on:** –. **Group:** WA-1. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (U18: the GPT model string mismatch; the user decides, this item never changes a judge model or prompt).
- **Test:** stub LLM server with a timeout, a 503 and a 429 per segment; replay the EP02 and EP08 audit inputs; one DIFF_MINI stage 1 on :8199.
- **Accept:** transient errors retry per segment (2, 5, 15 min cap) and are reported as `transient_llm`, not as a text failure; a segment never fails the whole audit on one timeout; U18 and U19 answered in the report; the verdict for an unchanged input is unchanged.
- **Risk / rollback:** a retry hides a real audit failure, so only timeouts, 503 and 429 retry. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In the four files listed, add per-segment retry with backoff for ReadTimeout, 503 and 429 only, and mark the stage-1 result `transient_llm` when only transport errors remain. Do not change audit prompts, thresholds, models or the verdict logic. Report whether `gpt-6-sol` or `gpt-6.1-sol` is live (documentary_voice_step2.py:279, documentary_voice_audit.py:20; U18), and whether the local 9router fallback at documentary_voice_step2.py:319 is used (U19). Test with a stub server, then replay EP02 and EP08. Budget: 75 min.

#### A9. Events: governor waits, token usage, BBC and yt_gate counts
- **Why:** Token and wait figures are missing from events, so the ledger's `tokens` table has no source and "n/a" appears in Q1 (Arch §4.9). **Gain:** per-film tokens per lane and governor wait seconds.
- **Files:** SCR\adaptive_governor.py, DM\io.py, DM\bbc_library.py, DM\yt_gate.py.
- **Depends on:** A1 merged (same files). **Group:** WA-2. **Size/model:** M / sonnet. **Flags:** –
- **Test:** unit tests for the event shape; DIFF_MINI ×2: event totals match the call counts in the logs, yt_gate pacing identical to baseline (calls per minute and bucket state).
- **Accept:** events carry governor slot wait time, input and output tokens per LLM call by lane, BBC cut-slot waits, and yt_gate calls per film; events.jsonl overhead under 1% of stage time; `yt_gate` pacing and `bucket.json` unchanged.
- **Risk / rollback:** logging only. `yt_gate` is observed, never modified. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Add events (no behaviour change): governor slot wait seconds per class (adaptive_governor.py); `lane`, `model`, `input_tokens`, `output_tokens` per LLM call in io.py (use the usage field when the API returns it, otherwise a `usage: null` marker); BBC cut-slot wait (bbc_library.py); one count per film of yt_gate calls (yt_gate.py, read-only counter). Do not change pacing, the bucket file or any limit. Test with unit tests, then DIFF_MINI ×2 and compare counts with the logs. Budget: 75 min.

#### A10. Timers for the untimed 25–30% of worker time
- **Why:** 25–30% of worker seconds belong to no timed step (U15), so the largest lever may be invisible. **Gain:** untimed share at most 10%.
- **Files:** DM\runner.py (timers only).
- **Depends on:** –. **Group:** W0-1. **Size/model:** S / sonnet. **Flags:** –
- **Test:** DIFF_MINI ×2; compare summed step time with worker wall time per shot.
- **Accept:** untimed share ≤10% of worker seconds; no logic changed (plan_diff identical); overhead below 1%.
- **Risk / rollback:** timers could change control flow if wrapped badly, so only context managers around existing blocks are used. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In DM\runner.py (_work_shot around :3618) find the work between the existing timed steps (render_with_qc, anim_make, grid_prefilter, media_gate_wait, precheck) and wrap those blocks in the same timer helper under new step names. Change no logic and no order. Run DIFF_MINI ×2 and report summed step time against worker wall time per shot, and list what the untimed time was. Budget: 60 min.

### Phase B: 20 films/day on the same hardware

#### B1. Pocket lane: FIFO across films, priority, recycle [NEEDS_IDLE]
- **Why:** Pocket runs at 2.83x alone but 0.19x under contention; at 20/day and 0.19x voice needs 104% of the day (Arch §6.3). **Gain:** Pocket ≥1.8x under load.
- **Files:** SCR\documentary_voice_engine.py, SCR\sopro_voice_client.py (lock and URL env only), VL\pocket-tts\pocket_serve.py, VL\Start-Pocket.ps1.
- **Depends on:** Q14 result, A1 merged. **Group:** WB-1. **Size/model:** M / sonnet. **Flags:** NEEDS_IDLE (Pocket restart).
- **Test:** on a Pocket copy on another port with 4 films' worth of sentences queued by 4 clients and 4 ffmpeg encodes running; then the Q14 arm check on the real settings.
- **Accept:** one FIFO lock across all films that survives reload; synthesis never runs two at once; realtime factor under load ≥1.8x (≥1.0x for the Phase A exit); the Q14 settings applied; audio for a fixed seed unchanged (identical bytes, else ECAPA ≥0.99); Sopro never on GPU.
- **Risk / rollback:** a stuck lock stalls all films, so the lock has a 10-min stale timeout. Rollback: git revert and restart Pocket in a drain window.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md and Arch §4.6. Use the recommended arm from Q14. In documentary_voice_engine.py keep one FIFO lock for all films using the `globals().get` pattern and the VOICE_LOCK idea in ENG\tools\batch_films.py:66-96. In Start-Pocket.ps1 start Pocket at AboveNormal priority (never Realtime); in pocket_serve.py set RECYCLE_MB (:64) from Q14. sopro_voice_client.py: lock and URL env only. Test on a copy first with 4 clients and 4 ffmpeg encodes; production restart only in a drain window. Budget: 90 min.

#### B2. ASR pre-gate per sentence
- **Why:** All 12 failed audits were text_completeness failures while voice match passed; 15 of 702 chunks (2.1%) were garbled, and a repair round costs 5–15 min (Arch §2.4). **Gain:** voice first-audit pass ≥80%.
- **Files:** SCR\documentary_voice_pregate.py (new), SCR\documentary_voice_engine.py.
- **Depends on:** B1 merged (same engine file). **Group:** WB-2. **Size/model:** M / sonnet. **Flags:** –
- **Test:** the garbled chunks from the 2026-10-30 films (EP07, EP10 and others) plus 100 good chunks: the pre-gate must catch the garbles and pass the good ones; one DIFF_MINI stage 1.
- **Accept:** at least 14 of the 15 known garbles caught per sentence before the master is built; at most 2 of 100 good chunks wrongly re-synthesised; added ASR time ≤10% of synthesis time; the audit and its thresholds untouched.
- **Risk / rollback:** a stricter text check loops; at most 2 resyntheses per sentence, then the audit decides. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Write documentary_voice_pregate.py: after each sentence is synthesised, run faster-whisper (the model already used for ASR) on the chunk and compare with the sentence text (word error rate and missing or repeated words). On a miss, re-synthesise at most twice (a new sentence wording is the repair when a repeat persists, since seed and temperature do not help). Hook it into documentary_voice_engine.py. Do not change the audit. Collect the 15 known garbled chunks from the run folders of the 2026-10-30 batch (paths from voice_audit.json) for the test. Budget: 90 min.

#### B3. CPU tokens in the governor [NEEDS_IDLE]
- **Why:** About 64% of CPU goes to short-lived child processes; HyperFrames takes about 170 s contended against 35 s alone (Arch §6.4). **Gain:** MSPS measured to move toward the 9.2 s target.
- **Files:** SCR\adaptive_governor.py, SCR\system_speed_profile.json, DM\resources.py, DM\motion.py, DM\cards.py, DM\three_render.py, DM\render.py.
- **Depends on:** A1 and A9 merged. **Group:** WB-1. **Size/model:** L / sonnet. **Flags:** NEEDS_IDLE (heavy benchmark).
- **Test:** DIFF_MINI ×3 per side and, in a drain window, a 3-film concurrent run on the bench: MSPS, HyperFrames render seconds contended, accepted shots per hour.
- **Accept:** a token pool of 10 of 16 logical CPUs (encode 4, decode 2, HyperFrames 2, 3D 2); no class exceeds its existing slot limit; added entries in system_speed_profile.json only add the token pool, none raises a limit; MSPS and HyperFrames contended seconds reported against baseline; the result is kept only if MSPS does not rise.
- **Risk / rollback:** tokens add waiting. A token wait above 60 s per render is reported. Rollback: git revert; the profile keeps its old keys.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md and Arch §4.7 item 1. Add a CPU-token pool to adaptive_governor.py (10 tokens: encode 4, decode 2, HyperFrames 2, 3D 2) and request tokens in resources.py, motion.py, cards.py, three_render.py and render.py. Existing slot limits in system_speed_profile.json stay as they are; add only the token keys. Log the wait seconds with the A9 events. Compare MSPS and HyperFrames render seconds against the wave baseline with 3 runs per side; run the concurrent test only in a drain window. Keep the change only if MSPS does not rise. Budget: 150 min.

#### B4. One ffmpeg per source
- **Why:** grid_prefilter takes 11–14% of step time and frame grabs start one ffmpeg per frame (Arch §4.7 item 2). **Gain:** −30% of grid_prefilter time.
- **Files:** DM\runner.py, DM\sources.py.
- **Depends on:** WB-1 merged. **Group:** WB-2. **Size/model:** M / sonnet. **Flags:** –
- **Test:** the same frames from old and new code on 5 sources: SSIM ≥0.999 per frame; DIFF_MINI ×3 per side for grid_prefilter seconds and plan_diff.
- **Accept:** `_frame_at` (runner.py:755), `_grid_frame` (runner.py:2536), `_contact_frame` (sources.py:2278) and `_contact_sample` (sources.py:2322) use one batched ffmpeg per source; SSIM ≥0.999; grid_prefilter seconds down 30% (target); shot selection distribution unchanged.
- **Risk / rollback:** exact seek differences shift a frame. SSIM is the gate. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Batch the frame grabs of `_frame_at` (runner.py:755), `_grid_frame` (runner.py:2536), `_contact_frame` (sources.py:2278) and `_contact_sample` (sources.py:2322) so one ffmpeg process per source file extracts all requested timestamps (input seeking; the e936d45 PNG cache keeps its key). Add an NVDEC decode as a second arm only to measure it. Compare frames with SSIM ≥0.999, then grid_prefilter seconds and plan_diff over DIFF_MINI ×3 per side. Report every run. Budget: 120 min.

#### B5. HyperFrames preset A/B [NEEDS_IDLE]
- **Why:** MOTION renders take a median 126–211 s and CARD 77–124 s in production (Arch §2.3). A preset or CRF change can cut that if SSIM stays ≥0.999. U4 asks whether HyperFrames accepts a CRF override.
- **Files:** DM\motion.py, DM\cards.py, TB\hf_ab\ (new).
- **Depends on:** B3 merged (same files). **Group:** WB-2. **Size/model:** M / sonnet. **Flags:** NEEDS_IDLE (heavy renders); NEEDS_USER only if the result needs 0.8.184 (D11, conditional).
- **Test:** 10 MOTION and 10 CARD scenes rendered with installed 0.8.181 (current), each preset or CRF arm, and 0.8.184 in a separate folder; 3 runs per arm, one render at a time.
- **Accept:** a table of render seconds and SSIM per arm; an arm is recommended only at SSIM ≥0.999 against the current output and at least 15% faster; fast-capture stays off; the installed version is not changed.
- **Risk / rollback:** a different encode changes bytes but not look; SSIM decides. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In new C:\Users\meteh\testbench\hf_ab\ render 10 MOTION and 10 CARD scenes (take them from a finished film's run folder) with the installed hyperframes 0.8.181, with each preset or CRF option the engine supports (U4; docs at https://hyperframes.heygen.com/packages/engine), and with 0.8.184 installed into a separate folder, never over the installed one. Three runs per arm, in a drain window. Compare SSIM and seconds. Change motion.py or cards.py only for an arm that passes SSIM ≥0.999 and is at least 15% faster. Budget: 120 min.

#### B6. 3D still pre-check [NEEDS_USER]
- **Why:** 59–83% of 3D shots fail (82 of 138, 156 of 189, 77 of 109), and each failed clip is a full render (Arch §4.7 item 4). **Gain:** failed 3D render seconds cut by at least 50%.
- **Files:** DM\three_render.py, DM\runner.py, TB\skull\judgeprobe\ (new cases).
- **Depends on:** A5 and B3 merged. **Group:** WB-3. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D10: a new gate position for the visual_fit judge).
- **Test:**
  - Run `probe.py` in judgeprobe on one still per past 3D shot (EP02–EP04) against the clip verdict: the still verdict must agree with the clip verdict.
  - DIFF_MINI ×3 per side.
- **Accept:** the unchanged visual_fit review judges one still before the clip render; still-FAIL agrees with clip-FAIL on at least 90% of the past shots, with 0 clip-PASS shots lost on the labelled set; failed 3D render seconds down ≥50%; the judge prompt, model and threshold unchanged.
- **Risk / rollback:** a still hides motion problems, so clips still go through the full review. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Proceed after the user approves the gate position (D10). In three_render.py render one still frame of the 3D scene first and send it to the existing visual_fit review with its existing prompt and model; on FAIL go to the A5 ladder without rendering the clip. Build a labelled set from EP02–EP04 3D shots (still versus final clip verdict) in TB\skull\judgeprobe\ and measure agreement with `probe.py` before enabling. The judge, its prompt and thresholds must not change. Report every run. Budget: 120 min.

#### B7. Tail admission [NEEDS_USER]
- **Why:** The stage-3 tail is 35% of the span (56–60 min at 1–5 workers); counting a tail film as 0.5 admits the next film earlier (Arch §4.5). **Gain:** idle share <10%.
- **Files:** ENG\ledger\admit.py.
- **Depends on:** A4 shadow mode working. **Group:** WB-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D9).
- **Test:** replay the active-worker counts of EP02–EP04 through the rule; shadow mode for 48 h.
- **Accept:** a film counts 0.5 only after ≥5 min with ≤5 active workers; RAM and paging rules of §4.5 still apply; in the replay the next film starts earlier by at least 20 min without any RAM breach; MAX is unchanged.
- **Risk / rollback:** two tails overlap with a new first pass and RAM rises; the free-RAM rule still gates. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. After the user approves (D9), add tail admission to ENG\ledger\admit.py: a film in stage 3 with ≤5 active workers for ≥5 min counts as 0.5 toward MAX. Read active-worker counts from run-folder events. Keep MAX and every other rule of Arch §4.5. Replay the EP02–EP04 worker counts and report start-time changes and free-RAM minima. Run it only in shadow mode. Budget: 45 min.

#### B8. Prescan as sources arrive; reruns reuse the pre-pipeline
- **Why:** The hook prescan and grid pre-pipeline restart on reruns; e936d45 fixed duplicate scans but not a scan-per-arrival (Arch §4.7 item 8). **Gain:** stage-3 reruns skip finished pre-pipeline work.
- **Files:** DM\scan_cache.py, DM\footage.py, DM\runner.py.
- **Depends on:** B6 merged (runner.py). **Group:** WB-4. **Size/model:** M / sonnet. **Flags:** –
- **Test:** DIFF_MINI stage 3 twice in a row (second is a rerun): rerun pre-pipeline time and plan_diff; a source added mid-run is scanned once.
- **Accept:** a rerun spends ≤20% of the first run's pre-pipeline time; each source is scanned once; plan_diff shows no change in categories; scan_cache survives reload.
- **Risk / rollback:** a stale scan used for a changed file; the key includes file stamp and thresholds as in e936d45. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Extend the e936d45 mechanism (done-marker keyed by windows, file stamps and thresholds): start the prescan of a source when it arrives in footage.py instead of at the stage-3 start, and let a stage-3 rerun reuse the finished pre-pipeline results. Keep the scan registry across reload. Do not change thresholds. Test DIFF_MINI stage 3 twice in a row ×2 and report pre-pipeline seconds and plan_diff. Budget: 90 min.

#### B9. Voice-ahead queue
- **Why:** Stage 1 takes 1,135–1,341 s when it passes and 1,804–5,706 s when it fails, and it holds film slots (Arch §4.1). **Gain:** stage 3 never waits for voice.
- **Files:** ENG\ledger\voice_queue.py (new), ENG\ledger\daemon.py.
- **Depends on:** A4 and B1 merged. **Group:** WB-2. **Size/model:** M / sonnet. **Flags:** –
- **Test:** simulation with 6 stub films; then shadow mode against the real queue.
- **Accept:** stages 1–2 run for the next 2–4 films while stage 3 films run; the Pocket FIFO lock is the only serializer; the voice queue takes no stage-3 slot; a film whose stages 1–2 fail is parked with its class and does not block the next.
- **Risk / rollback:** voice runs too far ahead and fills C:; admission keeps the C: rule. Rollback: disable the module in the daemon config.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md and Arch §4.5–§4.6. Add ENG\ledger\voice_queue.py and wire it into daemon.py: run stages 1 and 2 for the next 2–4 films in arrival order, one at a time per Pocket FIFO lock, and mark them `waiting_stage3`. Failures are parked with their class (Arch §4.4). Simulate with 6 stub films first. Do not start real films unless the dispatcher says so. Budget: 75 min.

#### B10. Fact-check in ≤120 s [NEEDS_USER]
- **Why:** Fact-check takes 161–337 s per film (28–112 searches, one after another) and 1.8–3.7 h/day at 40 films (Arch §6.8). **Gain:** ≤120 s.
- **Files:** SCR\documentary_factcheck.py.
- **Depends on:** Q6 merged (search health). **Group:** WB-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D10: fact-check precision and its position).
- **Test:** the same claims from 3 finished films, old and new code: flags must be identical; a SearXNG outage case.
- **Accept:** searches run with a bounded pool of 4; total time ≤120 s per film (target); flagged claims identical to the old code on the 3 films; prompts and thresholds unchanged; search errors never turn a flag into a pass.
- **Risk / rollback:** concurrent searches trip SearXNG limits; the pool of 4 is the cap. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. After the user approves (D10), change only the search execution in SCR\documentary_factcheck.py from serial to a pool of 4, with a per-search timeout and one retry. Keep every prompt, threshold and flag rule. Compare the flags and timing on the claims of 3 finished films (old versus new, 2 runs each) and test a SearXNG outage. Budget: 60 min.

#### B11. Stage 4: per-film temp, safe concurrency
- **Why:** Stage 4 takes 391 s per film and at 20/day concurrent runs must not share temp files or collide in delivery (Arch §6.8). **Gain:** concurrent stage 4 without errors.
- **Files:** DM\render_stage.py, DM\delivery.py.
- **Depends on:** A3 merged (delivery.py). **Group:** WB-2. **Size/model:** S / sonnet. **Flags:** –
- **Test:** two stage-4 runs at once on copies of finished films; a forced failure in one.
- **Accept:** each run uses its own temp folder; the final bytes match a solo run (sha256); one failure leaves the other untouched; stage 4 stays at ≤400 s solo.
- **Risk / rollback:** leftover temp folders; they are listed, not deleted. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Give render_stage.py a per-film temp folder under the run folder and make delivery.py names unique per film. Test two stage-4 runs at once on copies of two finished films and compare sha256 with solo runs. Do not delete leftovers; list them. Budget: 45 min.

#### B12. Pocket smaller models [NEEDS_USER]
- **Why:** A smaller Pocket model would cut synthesis load (Arch §4.6). It is allowed only if quality holds and the user listens.
- **Files:** TB\pocket_models\ (new).
- **Depends on:** Q14 merged. **Group:** WB-1. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D11: gated weights, licence, listening), NEEDS_IDLE (a second Pocket, 3 GB).
- **Test:** the 7M, 18M, _refl and int8 variants on the same 60 sentences and seed; ECAPA against the reference voice, WER, repeat check, realtime factor under the Q14 load.
- **Accept:** a model is proposed only with ECAPA ≥0.748, WER ≤2.8%, 0 repeated sentences and a realtime gain of ≥20%; the user listens to 5 samples before any switch; production Pocket is not touched.
- **Risk / rollback:** none for production; separate port and folder.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In a drain window, run each smaller Pocket model variant (7M, 18M, _refl, int8; check the licence and gated-weight terms in the Kyutai repo first and stop if access needs an account) on a copy on port 7874, never on :7863. Same 60 sentences and seed as Q14. Measure ECAPA similarity (baseline 0.748), WER (2.8%), repeats and realtime factor. Save 5 audio samples per candidate for the user. Do not change production. Budget: 120 min.

#### B13. redo_voice as a bridge endpoint [NEEDS_IDLE]
- **Why:** Repairs run outside the voice lock and rebuild the master even when nothing changed; a round takes 5–15 min (Arch §4.6). **Gain:** repair round time down by the master rebuild (39–204 s) when no chunk changed.
- **Files:** SCR\documentary_native_bridge.py, SCR\documentary_voice_repair.py.
- **Depends on:** Q7 and B1 merged. **Group:** WB-idle. **Size/model:** M / sonnet. **Flags:** NEEDS_IDLE (bridge restart; U7 asks whether a route can be added without it).
- **Test:** on :8199: repair of 2 garbled chunks through the endpoint; a repair with nothing changed; two repairs at once.
- **Accept:** the endpoint takes the Pocket lock; the master is rebuilt only when a chunk changed; failed ASR output is kept; the repair loop's 3-round cap is unchanged; U7 answered.
- **Risk / rollback:** a route that needs a restart fails on the running server, so the test checks it. Rollback: git revert and a restart in a drain window.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Add a `redo_voice` route to the bridge (test copy on :8199 first) that calls documentary_voice_repair.py under the Pocket FIFO lock, skips the master rebuild when no chunk changed, and keeps the failed ASR output beside the new one. Check whether `_reload_bridge_itself()` (bridge :142) makes a new route live without a restart (U7). Production restart only in a drain window. Budget: 75 min.

#### B14. G-Labs budget [NEEDS_USER]
- **Why:** Documentaries use 50–92 assets per film, shared with SkullStudio, against about 1,400 per night (anecdotal, U3); at 20/day demand is 71–131% (Arch §6.5). **Gain:** a shared daily budget that stops ANIM before G-Labs fails.
- **Files:** DM\glabs_budget.py (new), DM\anim.py.
- **Depends on:** A5 merged is preferred. **Group:** WB-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D6: daily shares between the two lines).
- **Test:** unit tests with a fake clock; a stub G-Labs; DIFF_MINI ×2 with the budget set low.
- **Accept:** one budget file read on every call; ANIM stops at the user's share and shots move down the A5 ladder; the budget is counted per day in local time; used assets per day are reported; U3 updated with the first measured number.
- **Risk / rollback:** a budget set too low lowers ANIM share; it is a config value. Rollback: set the share to unlimited or git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Use the shares the user approves (D6). Write glabs_budget.py: a small JSON file under %LOCALAPPDATA%\documentary_materials with a per-day count, safe against two writers (lock file), and read it in anim.py before every G-Labs request. When the share is spent, the shot goes to the A5 fallback ladder. Do not change SkullStudio. Count successful assets and failures separately. Test with a fake clock and a stub server. Budget: 60 min.

### Phase C: 30–40 films/day

All Phase C items that name money, a host, a channel or a publishing account wait for the matching user decision in Arch §10.

#### C1. Gate C1: purchase evidence [NEEDS_USER]
- **Why:** Gate C1 picks the purchase from data: 32 GB RAM if paging binds, the Hetzner AX42 worker if CPU binds, nothing if three 24-h days reach ≥317 accepted shots/h (Arch §8.4).
- **Files:** TB\gate_c1\ (new).
- **Depends on:** Phase B exit, Q1 data. **Group:** WC-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D12: money).
- **Test:** run on the Q1 baseline day and on the first Phase B days; check each rule on a synthetic day.
- **Accept:** a one-page verdict with numbers: accepted shots per hour and MSPS per day, page reads/s and pagefile at peak, CPU by role, and one of "no purchase / RAM / AX42"; the rule text is quoted from Arch §8.4, not changed.
- **Risk / rollback:** read-only.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md and Arch §6 and §8.4. In new C:\Users\meteh\testbench\gate_c1\ read the Q1 sampler output for three 24-h days and apply the rule: ≥317 accepted shots/h on all three days means no purchase; otherwise paging-bound means 32 GB RAM and CPU-bound means the AX42 worker. State which resource was binding with the numbers (page reads/s, pagefile use, CPU share by role). Do not order anything. Budget: 45 min.

#### C2. Remote HyperFrames worker (AX42) [NEEDS_USER]
- **Why:** If gate C1 says CPU, MOTION and CARD renders (66 per film) move off the PC (Arch §6.4).
- **Files:** DM\remote_render.py (new), DM\motion.py, DM\cards.py, `C:\Users\meteh\Kanallar\services\hf_worker\` (new).
- **Depends on:** C1 says CPU, B3 and B5 merged. **Group:** WC-2. **Size/model:** L / sonnet. **Flags:** NEEDS_USER (D12: the rental, €99/month + €49 setup).
- **Test:** shadow mode: render the same 20 scenes locally and remotely and compare; then a 10% share; failure cases (timeout, 5xx, switch off).
- **Accept:** SSIM ≥0.999 against local output; every remote call follows the Arch §4.2 contract (hard timeout, local fallback, switch file read per call, accounting in events); a remote failure never fails a film; remote share and fallbacks in the daily report.
- **Risk / rollback:** a rented host leaks scene data; no secrets in URLs, and only render inputs are sent. Rollback: switch file `enabled: false`.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md and Arch §4.2. Do nothing until the user has ordered the host and C1 says CPU. Write remote_render.py that sends a MOTION or CARD render job to the worker and falls back to the local path on a timeout or 5xx; read %LOCALAPPDATA%\documentary_materials\remote.json on every call. The worker folder holds the install and start scripts. Run in shadow mode first (compute remotely, use locally), compare SSIM, then 10%, then 100%. Never print keys. Budget: 180 min.

#### C3. Judges when GPT ends [NEEDS_USER]
- **Why:** After GPT ends its calls move to Flash, which then carries 57–108% of its realistic ceiling; flash-low agreed with the GPT reviewer only 78% of the time with 20% false PASS (Arch §2.7, §6.7).
- **Files:** TB\gpt_end\ (new), DM\io.py (approved routes only).
- **Depends on:** –; Q12 and A9 data help. **Group:** WC-1. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D10: judge replacement).
- **Test:** `TB\skull\judgeprobe\probe.py` on the labelled shots with each candidate (flash-low, flash high, a paid model if D12 allows), at least 3 runs per candidate.
- **Accept:** a candidate is proposed only if false PASS is at or below the GPT reviewer's own rate on the labelled set and agreement is ≥90%; otherwise the report says no replacement is safe; io.py routes change only for the candidate the user approves.
- **Risk / rollback:** false PASS lets bad shots through; the labelled set decides. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In new C:\Users\meteh\testbench\gpt_end\ build a labelled set of GPT-reviewer verdicts from finished films (PASS and FAIL, with frames) and run each candidate model through C:\Users\meteh\testbench\skull\judgeprobe\probe.py, 3 runs each. Report agreement and false PASS per candidate, with every run. Change DM\io.py routes only after the user approves a candidate. Do not change judge prompts or thresholds. Budget: 120 min.

#### C4. Paid LLM lane [NEEDS_USER]
- **Why:** If the shared lanes end, paid exposure is $2.9–11.2 per film (Arch §5, §6.7).
- **Files:** TB\paid_lane\ (new).
- **Depends on:** C3 result. **Group:** WC-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D12: money; the user creates the account and the key).
- **Test:** a cost model from A9 token events and the candidate's price list; a small call test on the user's key.
- **Accept:** cost per film and per month at 10, 20 and 40 films with ranges; latency and error rate on 50 calls; a recommendation for the user, not an order.
- **Risk / rollback:** none; no account is created by the agent.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Create no account and enter no payment details. In new C:\Users\meteh\testbench\paid_lane\ build the cost model from the A9 token events (input and output tokens per film per lane) and the price list of each candidate lane the user names. If the user supplies a key, run 50 calls and report latency and errors; identify the key only by its last four characters. Budget: 60 min.

#### C5. Source ledger per channel [NEEDS_USER]
- **Why:** At 40/day the same origin could appear in two films of one channel; the target is 0 reused origins within N days (Arch §7).
- **Files:** DM\source_ledger.py (new), DM\reservations.py.
- **Depends on:** A4 and A9 merged. **Group:** WC-1. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D13: the value of N per channel).
- **Test:** unit tests with a fake clock; DIFF_MINI ×2 with a seeded ledger.
- **Accept:** each used origin (video id, photo URL, BBC clip) is recorded per channel with the date; a shot cannot reserve an origin used in the same channel within N days; reuse blocked is reported per film; supply shortage is reported, never hidden.
- **Risk / rollback:** a strict N empties the pool; the report shows the shortage. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Use the N the user sets (D13). Write source_ledger.py (sqlite or JSON under %LOCALAPPDATA%\documentary_materials, one writer lock) and check it in reservations.py when a source is reserved for a shot. Record origin, channel and date at delivery. On a block, the planner takes the next candidate; if none exists, report the shortage. Test with a fake clock, then DIFF_MINI ×2 with a seeded ledger. Budget: 75 min.

#### C6. Identity packs and template ledger [NEEDS_USER]
- **Why:** CARD and MOTION families must not repeat in consecutive films of a channel (Arch §7 item 6).
- **Files:** DM\profiles.py, DM\template_ledger.py (new), DM\cards.py, DM\motion.py, channel pack files (new).
- **Depends on:** B5 and C2 decisions merged (cards.py, motion.py). **Group:** WC-3. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D13: the channels, their packs and voices).
- **Test:** generate 5 consecutive films' CARD and MOTION plans per channel on the testbench and measure repeats.
- **Accept:** each channel has a pack (palette, type, motion family set); the template ledger forbids the same family in two consecutive films of a channel; repeats of a family in consecutive films: 0; value is not random effects, each choice has a stated reason in the plan.
- **Risk / rollback:** a pack that clashes with a channel's look; the user reviews samples. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Use the channels the user names (D13; the SkullStudio channel profiles in C:\Users\meteh\SkullStudio\channels\ are a model). Add pack files per channel, template_ledger.py that records the families used per film, and use it in cards.py and motion.py to avoid the family of the previous film. Generate plans for 5 consecutive films per channel on the testbench and report repeats. Budget: 90 min.

#### C7. SkullStudio: shared G-Labs budget and voice choice [NEEDS_USER]
- **Why:** G-Labs is shared with SkullStudio; without a common count the two lines starve each other (Arch §6.5). Voice changes only after the user listens (Arch §7 item 8).
- **Files:** `C:\Users\meteh\SkullStudio\pipeline\` gen2.py, batch.py, gen_newposes.py, common.py, build8 script.
- **Depends on:** B14 merged, Q13 decided. **Group:** WC-1. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (the other line; D6 shares).
- **Test:** a stub G-Labs and a fake clock; one short SkullStudio episode on the test setup.
- **Accept:** all SkullStudio G-Labs calls read and count against the shared budget file; the voice engine still comes from `episode.json` → `voice.engine`; episode output is identical for a fixed seed; the other line's channel profiles are unchanged.
- **Risk / rollback:** a bug stops the other channel. Test first on the stub. Rollback: git revert in SkullStudio.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. With the user's approval, make the five SkullStudio files read and update the budget file written by B14 (DM\glabs_budget.py defines the format) before each G-Labs request. Do not change prompts, channels or the voice selection. Test with a stub G-Labs, then one short episode. Never start a production SkullStudio batch. Budget: 75 min.

#### C8. Film slots 3 → 4–5 [NEEDS_USER]
- **Why:** Little's law gives 4.2–4.9 films in flight at 40/day, but adding slots before MSPS falls makes every film slower (Arch §6.6).
- **Files:** ENG\ledger\admit.py, DM\bbc_library.py.
- **Depends on:** B-phase exit, C1 verdict, B7 merged. **Group:** WC-2. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D9).
- **Test:** shadow run with MAX 4 and 5 against the Q1 data; a 4-film run on the bench in a drain window.
- **Accept:** MAX changes only with the user's yes; at MAX 4 the 60-s mean page reads/s stays below the Q1 threshold and free RAM stays ≥2.5 GB; BBC cut slots (4 global) unchanged unless the user approves; throughput per film-minute does not fall.
- **Risk / rollback:** paging; the admission rule gates on it. Rollback: set MAX back in config.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Only after C1 and the user's approval, make MAX in ENG\ledger\admit.py configurable and test 4 then 5 in shadow mode against the Q1 samples; in bbc_library.py make no change to the 4 global slots unless the result shows they bind and the user approves. Report page reads/s, free RAM and accepted shots per hour for each MAX. Budget: 60 min.

#### C9. Publishing [NEEDS_USER]
- **Why:** Scripts and publishing for 40 films/day are unknown (U16); films are held in a buffer before they publish (Arch §7 item 9).
- **Files:** ENG\publish\ (new).
- **Depends on:** C10 for input, D13. **Group:** WC-1. **Size/model:** L / sonnet. **Flags:** NEEDS_USER (D13: OAuth, quota extension).
- **Test:** the YouTube API in a test channel only, with a private upload; quota cost table check; uplink measurement for a 1.78 GB file.
- **Accept:** upload via `videos.insert` with a quota plan (one project with an extension, never rotating projects or keys); a QA hold before publishing; every upload logs bytes and seconds (U10); the agent never uploads publicly.
- **Risk / rollback:** a public post of a bad film; uploads are private until the user releases them.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Create no account and accept no terms. After the user provides OAuth for a test channel, write ENG\publish\ with a private upload, a hold state, and a quota calculation from https://developers.google.com/youtube/v3/determine_quota_cost for 10, 20 and 40 films/day. Measure uplink on one file (U10). Never rotate keys or projects to avoid quota. Budget: 120 min.

#### C10. Script intake [NEEDS_USER]
- **Why:** Scripts arrive in ad hoc folders and 40/day needs a feed (U16).
- **Files:** ENG\intake\ (new).
- **Depends on:** D13 (who writes the scripts). **Group:** WC-1. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D13).
- **Test:** 5 sample script folders of different channels, including a malformed one and a duplicate.
- **Accept:** a watched folder format with channel, title and script file; validation (length, language English, duplicate title); each accepted script becomes a ledger row; rejected ones get a reason; round-robin across channels.
- **Risk / rollback:** a bad script wastes a film; validation runs before admission. Rollback: delete the folder.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Wait for the user's decision on who writes the scripts and in which format (D13). Write ENG\intake\ that watches an inbox folder, validates each script (English, words per film within the usual 2,000–2,650, no duplicate title in the channel) and writes a ledger row. Reject with a reason file. Do not start any film. Budget: 60 min.

#### C11. Disclosure metadata [NEEDS_USER]
- **Why:** YouTube requires disclosure of altered or synthetic content (Arch §7 item 7).
- **Files:** ENG\publish\metadata.py, DM\delivery.py.
- **Depends on:** C9 and A3 merged. **Group:** WC-3. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D13: disclosure policy).
- **Test:** metadata for 3 finished films checked against the policy pages https://support.google.com/youtube/answer/14328491.
- **Accept:** each film's manifest carries the disclosure flag and the credits text built by A2; the policy text used is quoted with its source; nothing publishes.
- **Risk / rollback:** a wrong disclosure; the user approves the policy first.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. With the user's policy (D13), make metadata.py build title, description, credits (from credits.py) and the synthetic-content flag, and have delivery.py write them into the manifest. Read the policy pages first and quote them in the report. Do not publish. Budget: 45 min.

#### C12. VDS inventory [NEEDS_USER]
- **Why:** 9router's own limits are not inventoried (U2) and the local 9router binds 0.0.0.0:20128.
- **Files:** TB\vds_inventory\ (new).
- **Depends on:** D14 (access). **Group:** WC-1. **Size/model:** S / haiku. **Flags:** NEEDS_USER (D14).
- **Test:** the user-approved read-only commands on the VDS.
- **Accept:** a read-only list of services, ports, limits, versions and free resources on the VDS; nothing changed, no secrets in the report.
- **Risk / rollback:** none if read-only.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. Use only the access the user approves (D14); the VDS is at 100.104.78.117. Run read-only commands (uptime, memory, listening ports, 9router version and configured limits). Change nothing, copy no keys, and write the inventory to C:\Users\meteh\testbench\vds_inventory\. Budget: 40 min.

#### C13. Network path to the VDS [NEEDS_USER]
- **Why:** 9router is reached through the DERP relay, not a direct path (Arch §2.7, §4.2 item 4).
- **Files:** TB\net_path\ (new).
- **Depends on:** D14. **Group:** WC-1. **Size/model:** S / sonnet. **Flags:** NEEDS_USER (D14: network changes).
- **Test:** Tailscale status and RTT and throughput samples over 24 h; a try at a direct path only if the user approves a change.
- **Accept:** a daily log of connection type, RTT and throughput; a proposal for a direct path with the exact change; no change without approval.
- **Risk / rollback:** none for measuring.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In new C:\Users\meteh\testbench\net_path\ record `tailscale status` and `tailscale ping` results, RTT to the 9router port and a small throughput test every 10 minutes for 24 h. Read https://tailscale.com/kb/1257/connection-types and propose the exact change for a direct path. Make no network change. Budget: 45 min.

#### C14. Async stage jobs in the bridge [NEEDS_IDLE]
- **Why:** drive.py holds one blocking POST per stage (timeout 24 h); a job id with polling removes the long connection (Arch §4.1).
- **Files:** SCR\documentary_native_bridge.py, ENG\ledger\stage_client.py.
- **Depends on:** Q7, B13 and A4 merged. **Group:** WC-idle. **Size/model:** M / sonnet. **Flags:** NEEDS_IDLE (bridge restart; U7).
- **Test:** on :8199: start, poll, cancel and a reload mid-job; compare results with the blocking route.
- **Accept:** `POST` returns a job id; `GET` returns status; the blocking route still works unchanged; a duplicate job is rejected with the exit-11 text; results identical to the blocking route.
- **Risk / rollback:** Dify calls the bridge on the old route; it is kept. Rollback: git revert and a restart in a drain window.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. In the test bridge copy add job routes (start, status, cancel) beside the existing blocking stage routes, which stay as they are for Dify and drive.py. Write ENG\ledger\stage_client.py that uses the job routes. Check U7. Production restart only in a drain window. Budget: 90 min.

#### C15. VIDEO supply at volume
- **Why:** Failed VIDEO allocations were 98 of 193 (EP02), 75 of 211 (EP03) and 32 of 180 (EP04); the planner keeps the 40% VIDEO target, so supply is the limit (Arch §2.3, §4.7 item 7). YouTube calls at 40/day are 7–20% of the gate's 60k/day.
- **Files:** DM\runner.py, DM\sources.py.
- **Depends on:** A2 and B4 merged. **Group:** WC-2. **Size/model:** M / sonnet. **Flags:** –
- **Test:** DIFF_MINI ×3 per side; yt_gate calls per film and per minute before and after.
- **Accept:** failed VIDEO allocations down against the wave baseline; yt_gate pacing and the 41.7 calls/min budget unchanged, every call through the gate; delivered VIDEO share closer to 40%; no new PARTIAL acceptances.
- **Risk / rollback:** more candidates mean more gate calls; the gate paces them. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. From the EP02–EP04 run folders list why VIDEO allocations failed (no candidate, rejected by prefilter, rejected by review) and widen only the candidate search in sources.py and runner.py for the biggest cause, always through yt_gate with its pacing unchanged. Compare failed allocations and yt_gate calls per film over DIFF_MINI ×3 per side. Report every run. Budget: 90 min.

#### C16. Review trimming and a top-3 single review call [NEEDS_USER]
- **Why:** Per-shot Flash review is 24–26% of input tokens and GPT review 12%; after GPT ends, Flash calls rise to 55.9k–81.9k per day (Arch §2.3, §6.7).
- **Files:** DM\runner.py, DM\io.py.
- **Depends on:** C3 result. **Group:** WC-3. **Size/model:** M / sonnet. **Flags:** NEEDS_USER (D10: a changed gate).
- **Test:** `TB\skull\judgeprobe\probe.py` on the labelled set with the top-3 single call against the current separate calls, ≥3 runs; DIFF_MINI ×3 per side.
- **Accept:** review calls per film down by at least 25% with false PASS at or below the current rate and agreement ≥95% on the labelled set; judge prompts, models and thresholds unchanged; otherwise no change is made.
- **Risk / rollback:** a looser effective gate; the labelled set decides. Rollback: git revert.
- **Brief:** First read §1 of C:\Users\meteh\.gemini\scripts\documentary_materials\docs\WORKPLAN_40_PER_DAY.md. With the user's approval (D10), review the top 3 candidate renders of a shot in one call instead of one call each, using the existing review prompt wording per image. Compare verdicts with the current path on the labelled set from C3 using probe.py (3 runs), and report calls per film and false PASS. Keep the change only if both numbers hold. Budget: 90 min.

