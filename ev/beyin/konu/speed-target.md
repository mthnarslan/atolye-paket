---
tur: konu
aciklama: Speed target and where it stands (2026-10-24); next lever is the per-shot GPT review
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/speed-target.md
olusturma: 2026-10-24
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
**Target** (user, 2026-10-23/24): a ~4–5 min film goes from input folder to ZIP in ≤15 min (ideal 10), fully automatic, rules met. The user paused the work at 03:20 on 2026-10-24 ("kalsın şimdilik").

**Best so far:** TOPIC_2 (3:52 wildlife film) in 18.5 min. Later runs were 20–21 min, or blocked by YouTube.

**Done and verified:**
- `window_index.py`: one decode per window. Per-shot cut, motion, freeze and face checks dropped to ~0 s.
- bgutil PO token + mweb client (server at C:\Users\meteh\tools\bgutil-pot, auto-started by `sources.ensure_pot_server`). Removed YouTube's "not a bot" block: 0 errors after the change.
- SigLIP person check on face hits (tigers and forests were false talking heads).
- Sopro stop fix, invented-ID tolerance, catalog kept across expansion rounds, merge rounds.

**Remaining bottleneck (last run):** the GPT review on the VDS gateway (:8765, 4 upstream slots, shared with the user's friend). Model median 23 s / p90 120 s, queue p90 151 s. In-queue sentence search (`_search_and_retry`) raised reviews from 58 to 93.

**Options offered, not chosen yet:**
- Skip GPT when the Flash precheck and SigLIP both pass.
- Flash-high as reviewer (79% agreement measured).
- Batch contact-sheet review (Gemini Argon research report).

**Why:** the user wants speed first, before new films.
**How to apply:** start from these measurements; consider whether in-queue search should be capped. Related: [[documentary-20min-budget]].
