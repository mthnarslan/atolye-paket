---
tur: ders
aciklama: During film production always keep a supervisor/watcher running; re-arm it on every wake
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/rearm-watchers.md
olusturma: 2026-10-25
guncel: 2026-10-25
yazan: auto-memory
onay: 
etiket: 
---
While films run, a background watcher (scratchpad supervisor.py, which exits on each incident) must be re-armed immediately after every notification, and every lane/retry chain needs its own completion watcher.

**Why:** On 2026-10-25 the supervisor exited at 15:42 and was not re-armed; TOPIC_2/3 sat 1-2 shots short and TOPIC_5/6/7 died unretried for ~4 hours. The user: "neden durmuş sen neden fark etmedin mesela mevzu bu".

**How to apply:** On any task notification during production: read it, act, then `supervisor.py --prime` and restart it in the background before ending the turn. Related: [[speed-target]].
