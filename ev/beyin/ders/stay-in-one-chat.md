---
tur: ders
aciklama: User stays in one long chat; never propose new sessions or /clear as a token-saving measure
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/stay-in-one-chat.md
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: auto-memory
onay: 
etiket: 
---
Token savings must work inside the same long-lived chat. Do not propose "start a new session", "/clear" or stage-boundary handoffs to a fresh chat as a saving.

**Why:** on 2026-11-10 the user rejected the rule "new session after each stage or after >1 h idle": he builds up understanding in one chat, and switching would mean switching constantly ("yeni sohbet istemiyorum ... bu benim işime yaramaz").

**How to apply:** look for in-session levers (what enters the context, compaction that keeps state, delegation, fewer calls). Solutions should come from real users' reported experience, not vendor claims. Related: [[token-efficiency-not-austerity]], [[main-model-opus]].
