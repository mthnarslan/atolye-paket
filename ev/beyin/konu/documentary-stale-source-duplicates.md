---
tur: konu
aciklama: Önceki koşunun tam YouTube kopyaları yerel taramaya giriyordu; 14,2 saatlik video medya kapısını blok ediyordu.
kaynak: auto-memory C--Users-meteh/memory/documentary-stale-source-duplicates.md
olusturma: 2026-10-22
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
`input_folder` onceki kosunun cikti klasoru olunca `sources/` altindaki **tam YouTube indirmeleri** (59 dosya, 14,2 saat video) `scan_folder()` ile yerel varlik olarak katalogA giriyordu; ayni kimlikler bu kosuda range penceresi olarak zaten indirilmisti. `_motion_score` tum araligi cozdugu icin bayat dosyalar 30 sn zaman asimina kadar medya kapisini (genislik 1) tikadi: ~21 dk bosa, 14 dk'da 0 shot.
Duzeltme (`sources.py`): `_superseded_video_stems(folder, out)` iki `sources` klasorundeki mp4 kok adlarini toplar, `scan_folder(folder, out=out)` bunlari atlar (`runner.py` ayni imzayi cagirir, yoksa katalog parmak izi her kosuda degisir). Cikti degismez; yerel tarama 7 satira dustu.
**Ders:** girdi klasoru onceki kosunun klasorunse `sources/` altindaki ham indirmeler varlik degil ham malzemedir. Ilgili: [[documentary-range-download-architecture]].
