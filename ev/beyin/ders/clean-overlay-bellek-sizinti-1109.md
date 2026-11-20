---
tur: ders
aciklama: clean_overlay --jobs toplu mod is basina bellek biriktirir: EP03 81 is, 07:44'te ~5 GB -> 08:26'da 15,3 GB private; commit 599 MB'a dustu
kaynak: GaiaTrace finish 1109 olcum
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# clean-overlay-bellek-sizinti-1109

Olcum 2026-11-09: EP03 clean_overlay pid 30792 (81 is, cogu ProPainter) private bytes 07:44 basinda ~5-6 GB, 08:06 10,6 GB, 08:26 15,3 GB; is hizi 17 sn/is'ten ~1 is/dk'ya dustu (sayfalama). Commit bosu 599 MB'a indi, ayni anda S6 isci testi (heavy_replay.py 2,3 GB) vardi. Cozum adaylari: toplu modda her N iste (or. 20) alt sureci yeniden baslat ya da is arasi torch.cuda.empty_cache + gc + ProPainter durumunu sil. GPU temizligi surerken RAM-agir test kosturma; commit < 2 GB ise test isci sureclerini askiya al (psutil suspend).
