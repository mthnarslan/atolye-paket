---
tur: konu
aciklama: YouTube indirme mimarisi: tek geniş pencere (26 sn span / 32 sn dosya) ölçülmüş 189.7 sn / 75 kaynak / 311 MB.
kaynak: auto-memory C--Users-meteh/memory/documentary-range-download-architecture.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
YouTube'dan tam dosya yerine yalniz kullanilacak kesitler cekilir (olculmus ve uygulanmis; `sources.py` `plan_windows` + `fetch_source_windows`): kaynak basina **tek pencere**, span 26 sn -> padding'li dosya 32 sn, 8 paralel, `socket_timeout=30`.

Olcum (75 kaynak): tek pencere 189,7 sn / 311 MB (75/75); iki pencere ayni sureye 501 MB ve bir kaynak kaybi; 38 sn pencere 204,9 sn; tam dosya 283 sn / 8290 MB. Tek pencere yeterli: teslim edilen filmde 56/60 kesisim kaynagin %45-51 bandinda, 26 sn pencere 60 kesisimin 57'sini kapsar.
`socket_timeout` 15 -> 30: 15'te 8 paralel ffmpeg CDN'den okurken bir kaynak Windows timeout durumuyla kayboldu.
**How to apply:** pencere sayisi/span degisince yeniden olc (`tmp/bench_final.py`). Ilgili: [[documentary-20min-budget]], [[documentary-pipeline-project]].
