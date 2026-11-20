---
tur: ders
aciklama: "In tests, voice only a short sample (~30 s), not the whole script; remove downloads that turned out useless"
kaynak: auto-memory C--Users-meteh-Kanallar/memory/deneme-kisa-ses.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: auto-memory
onay: 
etiket: 
---
When testing voice/TTS, generate only the trial portion (the first ~30 s or 1–3 sentences), not the whole narration. Delete anything downloaded and tested that won't be useful (models, clones, venvs).

**Why:** user, 19 Nov: "bütün sesi seslendirmene gerek yok denemelik kısmını seslendir… işimize yaramayacaksa kaldır gitsin".

**How to apply:** In every voice A/B or detector test, use short windows; write a delete step for failed tools into the agent prompt. Related: [[ajan-butce-1119]]
