---
tur: kaynak
aciklama: Desktop KEY.txt: 26 Gemini keys (23 live) now a Flash fallback lane in io.py (gdirect), plus 5 YouTube Data API keys; never print values
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/api-keys-desktop.md
olusturma: 2026-10-30
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
`C:\Users\meteh\Desktop\KEY.txt` holds two sets of keys. Never print or store a key value; refer to a key by its index and last 4 characters.
- 5 YouTube Data API v3 keys (AIza…), all valid. They could later move search off yt-dlp.
- 26 Gemini API keys (AQ.…), listed after a "GEMINI" heading.
  - Keys 3–5 answer 403, "free tier not available". They are dead.
  - The user says the keys are billed, bought through a campaign, and approved using them. Google still reports `-FreeTier` quota IDs and a limit of 0 for pro, image and lyria models.

Since 2026-10-30, prod 68d1c8c and governor 515cd22, the keys form an extra Flash lane:
- How it works:
  - `gemini_keys.py` sends requests to Google's OpenAI-compatible endpoint with `gemini-3.6-flash` (env `DOCUMENTARY_GEMINI_MODEL`).
  - io.py routes a `flash` call to it only when 9router Flash is cooling down or all of its slots are busy, and only when the call has no URL.
  - The governor channel is `gdirect`, with 6 slots.
  - A refused key passes the request to the next key within the same attempt.
- The daily count is kept per key and model, per Pacific day:
  - It lives in `%LOCALAPPDATA%\documentary_materials\gemini_usage.json`.
  - A 429 marks the key/model pair spent; a 403 marks the key dead.
  - For a summary, run `python -m documentary_materials.gemini_keys`.
- Testbench: `testbench\gdirect_test.py` passed 8/8 at 1.2–3.3 s.

Models from the probe (`testbench\gem_probe.py`, `gem_keygrid.py`):
- 3.6-flash: fast and good; this is the lane model.
- 3.1-flash-lite: caught all 4 errors in the Hoover fact-check, about 8–10 s.
- 3.5-flash: fast.
- Gemma: hallucinates.
- 3.5-transcribe and 3.8-flash-tts models also exist.

2026-10-30: the dead keys 3–5 were deleted from KEY.txt, leaving 23 keys. Dead marks now use the last 4 characters (commit after 68d1c8c). Run the summary from `C:\Users\meteh\.gemini\scripts`.

KEY.txt also has Groq, OpenRouter, NVIDIA NIM and Cohere keys at the end (no headings). 2026-10-30 probes found none better than the 3.6-flash lane (small limits, slow or weaker fact-checks); nothing integrated.

Related: [[youtube-gate]], [[gpt-replacement-model]].
