---
tur: ders
aciklama: Size tests to the question; give every test subagent a time budget; no full-film runs when a mini film or planning-level diff answers it
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/test-time-budget.md
olusturma: 2026-10-29
guncel: 2026-10-29
yazan: auto-memory
onay: 
etiket: 
---
Design tests to answer the question in the shortest run, and put an explicit time budget in every test subagent brief.

**Why:** 2026-10-29 I briefed a differential test as three full TEST_A film runs (~1.5-2 h) and two other agents with no budget (they kept calibrating). The user: "doğru testlerle bu kadar uzun sürmemesi lazım". Shortened to a ~3-scene mini film + planning-level diff and 20-40 min budgets.

**How to apply:** first ask where the change acts (planning vs materials vs render) and test at that stage; use a mini film (first ~3 scenes) for stage-3 effects; full films only to confirm a promotion. State the budget (e.g. "finish within 30 min, report what you have"). Related: [[speed-target]].
