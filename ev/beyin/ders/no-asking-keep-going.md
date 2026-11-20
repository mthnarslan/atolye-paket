---
tur: ders
aciklama: "Speed/bottleneck work: don't ask the user for go-aheads; use GPT + Flash-high (fikir.py) as workers, cross-test, apply when no batch runs, come back with measured results"
kaynak: auto-memory C--Users-meteh-Kanallar/memory/no-asking-keep-going.md
olusturma: 2026-11-07
guncel: 2026-11-18
yazan: auto-memory
onay: 
etiket: 
---
The user (7 Nov 2026): "bana sorma asla"; work through every bottleneck (stage-3 tail, RAM, 3D…) in parallel, using GPT and Flash-high via `beyin/araclar/fikir.py` instead of Claude subagents. Cross-test, then come back only with firm, measured results.

**Why:** they lost time on repeated go-ahead questions and want the fixes landed today.

**How to apply:**
- Don't end turns with "apply?" questions.
- When no batch runs on :8099, apply a change that passed testbench to prod yourself.
- The SISTEM rules still hold: no prod commits during a batch, and no loosening of judges/QA without evidence.

See [[background-watchdog-agent]].

## 2026-11-18 (auto-memory guncellemesi: C--Users-meteh-Kanallar)

The user (7 Nov 2026): "bana sorma asla"; work through every bottleneck (stage-3 tail, RAM, 3D…) in parallel, using GPT and Flash-high via `beyin/araclar/fikir.py` instead of Claude subagents. Cross-test, then come back only with firm, measured results.

**Why:** they lost time on repeated go-ahead questions and want the fixes landed today.

**How to apply:**
- Don't end turns with "apply?" questions.
- When no batch runs on :8099, apply a change that passed testbench to prod yourself.
- The SISTEM rules still hold: no prod commits during a batch, and no loosening of judges/QA without evidence.

See [[background-watchdog-agent]].

**18 Nov 2026 addition (metin/ses human-likeness work):** the user said: "sormadan devam et, olay sende". Keep improving text and voice in every language until the result is human-level, and add the current status to the Ortak Atölye site without asking first (post_update card + guide page update).
