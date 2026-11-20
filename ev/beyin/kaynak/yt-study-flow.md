---
tur: kaynak
aciklama: How we study YouTube videos together with Flash; 9router can't take YouTube URLs, frames+transcript works
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/yt-study-flow.md
olusturma: 2026-10-30
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
User sends YouTube videos to study together and pull ideas into the system (started 2026-10-29). Flow lives in `C:\Users\meteh\.gemini\yt_study\`: per video `<id>\` (meta.json, v.*.vtt, transcript.txt, video.mp4 480p, frames/ every 15 s, flash_review.md); tools in `_tools\` (`flash_review.py <dir>` sends SISTEM.md + transcript + all frames to `ag/gemini-3.8-flash-high`).

- Fetch through `yt_gate.call` with `sources._yt_common()` + `sources.YOUTUBE_ARGS` (plain yt-dlp CLI fails: no JS solver/POT → "only images").
- 9router drops `video_url`/`file` YouTube parts; Flash then says it can't see the video. Frames as base64 `image_url` work: 26 min video = 103 frames ≈ 135k prompt tokens.
- Flash only knows SISTEM.md, not the code, so it proposes things that already exist (SkullStudio qa.py vision review, run_episode resume). Check its ideas against the code before presenting.

Reading transcript/Flash report/READMEs goes to a Sonnet subagent; only its summary enters the main chat (SISTEM.md rule, asked 2026-10-29). Main chat still verifies claims against code.

Subtitles: since 2026-10-30, fetch only `.*-orig` tracks, with ignoreerrors.
- Asking for `en`/`tr` (machine-translated) got HTTP 429 on timedtext (yt-dlp #13831).
- That 429 went through yt_gate and paused the films as well.
- The films themselves never fetch subtitles and logged no 429.

One command per video: `_tools\fetch.py <id>` (meta, subs, transcript, 480p, frames), then `_tools\flash_review.py <dir>`.

Related: [[rearm-watchers]].
