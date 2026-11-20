---
tur: ders
aciklama: Never install a hook that blocks or delays the user's prompts; cachewarn was removed on user demand
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/no-blocking-hooks.md
olusturma: 2026-10-30
guncel: 2026-10-30
yazan: auto-memory
onay: 
etiket: 
---
Never add a UserPromptSubmit (or any) hook that blocks, holds or asks the user to resend their message. The cachewarn hook, which blocked the first message after a cache expiry, was removed on 2026-10-30 at the user's firm request.

**Why:** the user said they must be able to message any session freely, whenever they want.

**How to apply:** save tokens through non-blocking means only, such as warnings in the status line, compaction settings or delegation. Never gate the user's input. Related: [[token-saver-tools]], [[commander-subagent-models]].
