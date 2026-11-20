---
tur: konu
aciklama: Parked plan (2026-10-29) to add OpenCode Go $10 and AMD Radeon Cloud to 9router as a text-only backup lane next to GPT/Flash
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/opencode-go-backup-lane.md
olusturma: 2026-10-29
guncel: 2026-10-29
yazan: auto-memory
onay: 
etiket: 
---
Parked on 2026-10-29; the user wants to do it later, not now: add a second LLM lane to the VDS 9router (100.104.78.117:20128) for text-only jobs.
- OpenCode Go, $10/month. Each model has its own monthly dollar cap: DeepSeek V4.1 Flash $80, Gemini 4 Argon $30, Qwen3.8 Flash $30, MiMo/GLM Flash $60. Each cap also has a 5-hour window (20% of it) and a weekly window (50%). The endpoint is OpenAI-compatible: https://opencode.ai/inference/go/openai/v1/chat/completions. Keep "Extra Usage" off.
- AMD Radeon Cloud: free, no card. Third-party sites quote ~30 RPM, 8 concurrent requests and ~$10/day, but none of this is verified.
- The free `oc/*` and `mmf/mimo-auto` models already in 9router all failed on 2026-10-29: unavailable, 429 free limit, unsupported model name.
- Rejected: Token Harbor and Freebuff (free requests are used for training, or there is no API) and the video's fake-card and VPN tricks.

**Why:** Flash is the only text lane today. The DeepSeek $80 cap is roughly 50k requests a month, which is enough for a backup lane but not for the 40 films/day goal.

**How to apply:** when the user brings this back, wait until they have subscribed and added the key in the 9router panel. Then run a cross-test against Flash on real tasks (narration reword, shot plan, cutaway codegen, CTA line) and report pass rate, latency and cost per call. Vision checks stay on Gemini. Related: [[gpt-replacement-model]]
