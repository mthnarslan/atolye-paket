---
tur: konu
aciklama: 2026-11-01 Google banned 23/30 9router Antigravity accounts (403 TOS_VIOLATION) after heavy video scanning; how to detect, what not to do
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/antigravity-tos-ban.md
olusturma: 2026-11-01
guncel: 2026-11-01
yazan: auto-memory
onay: 
etiket: 
---
On 2026-11-01 (by 08:32 at the latest), Google disabled 23 of the 30 Antigravity accounts behind 9router. Every call returns 403 PERMISSION_DENIED with reason TOS_VIOLATION and an appeal form link.
- Likely trigger: the heavy inline-video scanning of the editscan jobs (deep50, flow, craft, teach).
- The 9router log only shows "HTTP 403". To see the real reason, call `daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist` on the VDS with the account's accessToken from the DB and read the response body.
- The 6 accounts still working hit the 429 quota fast. Production Flash then falls back to `gemini_keys.py` (io.py cooldown), but calls that carry a YouTube URL cannot fall back.

**Why:** the bulk scans burned the shared LLM pool production depends on. The user only noticed when the deliverables stalled.

**How to apply:**
- Do not run mass video/LLM scans on 9router again without the user's OK and a throttle.
- Never try to dodge the ban (new accounts, IP changes). Appeals are the user's decision.
- Related: [[gemini-key-pool-block]], [[fix-systemic-errors-proactively]].
