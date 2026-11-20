---
tur: ders
aciklama: "Claude limit rule (user, 19 Nov via GAIATRACE): no Opus subagents; Haiku first; every agent gets ~25 tool turns and a report of ≤40 lines"
kaynak: auto-memory C--Users-meteh-Kanallar/memory/ajan-butce-1119.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: auto-memory
onay: 
etiket: 
---
No Opus subagents (advisors included). Start subagents on Haiku; if Haiku is not enough, raise its effort or switch to Sonnet, depending on the job. Always set model and effort explicitly in the Agent call. Give every agent a budget: ~25 tool turns, read big files with grep or in parts, report ≤40 lines.

**Why:** 19 Nov: 40% of the 5-hour limit was used up in 50 minutes, mostly by ~12 Sonnet research agents (33–41 steps each, 150–168k context).

**How to apply:** Write the budget into every agent prompt. Prefer headless `claude -p --setting-sources ""` (~900 tokens) for cheap repeated calls such as judging. Related: [[background-watchdog-agent]]
