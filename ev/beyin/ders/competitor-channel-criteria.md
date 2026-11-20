---
tur: ders
aciklama: Competitor/model channels we suggest must be faceless, monetized (verified), English; how to check monetization
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/competitor-channel-criteria.md
olusturma: 2026-10-30
guncel: 2026-10-30
yazan: auto-memory
onay: 
etiket: 
---
Only suggest model channels that are **faceless** AND **monetized**, in English (2026-10-30). The user rejected YureiTales (NexLev said "Not Monetized") and 365 Delicious Days (real hands cooking on camera). A channel where a person only rarely talks on camera is fine, because we can replace them with an AI character.

**Why:** a channel that isn't monetized or isn't faceless can't be copied by our pipelines, and suggesting one wastes time.

**How to apply:**
- Check monetization on the watch page: `"key":"yt_ad","value":"1"` in serviceTrackingParams.
  - Present on every page for monetized channels, even when no ad was served (Veritasium control). Missing for YureiTales, which matches NexLev.
  - The old `is_monetization_enabled` field no longer exists.
  - Fetch pages through `yt_gate.call` WITH Firefox cookies.
  - Logged-out fetches mostly get `playabilityStatus LOGIN_REQUIRED` (bot check), and those pages lack yt_ad, which gives a false "not monetized". Count only pages with status OK.
- Check faceless with Flash on frames from inside the video (`i.ytimg.com/vi/ID/hq1..3.jpg`).
- Tools: `C:\Users\meteh\ytmarket_run\bin\niche_hunt.py` (F1–F10 filters) then `check_pass.py` (yt_ad + faceless + language).

Related: [[production-language]] [[api-keys-desktop]]
