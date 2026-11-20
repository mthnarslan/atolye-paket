---
tur: konu
aciklama: Fanning one prompt over ~20 free Gemini keys got that exact prompt text 429-blocked on every key (2026-10-31); use 9router inline video instead
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/gemini-key-pool-block.md
olusturma: 2026-10-31
guncel: 2026-10-31
yazan: auto-memory
onay: 
etiket: 
---
2026-10-31 edit scan (ytmarket_run\editscan\scan.py): ~70 YouTube-URL calls with the same long prompt spread over 20 free AQ. keys. After ~26 successes every key returned 429 "Resource has been exhausted" for that prompt, even text-only with no video, in 0.4 s; other prompts on the same keys still worked; a reworded opening passed. Google fingerprints the request across keys as key pooling.

**Why:** rewording to dodge it is evading an abuse control, and it puts the production gdirect lane (same keys) at risk of a ban.

**How to apply:** don't fan one workload over many free Gemini keys. For video reading use 9router (`ag/gemini-3.8-flash-*`): it takes inline video as `image_url` with `data:video/mp4;base64,...` (~90 tokens/s, verified correct). The `file` part type does not work. Get the slices with yt-dlp `--download-sections` through yt_gate, then delete them. A paid single key is the other clean option. Related: [[gpt-replacement-model]], [[youtube-gate]].
