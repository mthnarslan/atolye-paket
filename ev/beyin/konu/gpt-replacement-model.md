---
tur: konu
aciklama: When GPT (gpt-6-sol on VDS :8765) access ends, switch review roles to 9router ag/gemini-3.8-flash-low
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/gpt-replacement-model.md
olusturma: 2026-10-26
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
---
tur: konu
aciklama: When GPT (gpt-6-sol on VDS :8765) access ends, switch review roles to 9router ag/gemini-3.8-flash-low
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/gpt-replacement-model.md
olusturma: 2026-10-26
guncel: 2026-10-26
yazan: auto-memory
onay: 
etiket: 
---
GPT access is ending soon (user, 2026-10-26). Benchmark on 60 replayed GPT shot reviews + live QA groups (scratchpad model_bench/, 2026-10-26):
- ag/gemini-3.8-flash-low: 78% agreement (87% on GPT-stable set), false PASS 20%, median 8.8 s, 6 parallel OK. Best.
- flash-medium 68%, flash-high 55-58% with ~60% false PASS (worst).
- On 9router, Gemini Pro/Argon, Claude Opus/Sonnet 5.5, Gemini 3.6/3.7 returned 404; claude-*-4-6 and gpt-oss don't see images (opus-4-6-thinking hallucinates). Re-test if they come back.
- flash-low weak on ANIM (morphs) and CARD (false FAILs). Raise review token limits to >=2500.

**Why:** the user wants a ready switch when GPT stops.
**How to apply:** point io.py codex role (and qa_audit.py) at ag/gemini-3.8-flash-low via the 9router gateway when GPT ends; FLASH_REVIEW was already switched to flash-low (commit c7db281).
GPT model/effort bench sonuclari: [[gpt-model-secimi]].
