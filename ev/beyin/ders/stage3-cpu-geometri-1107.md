---
tur: ders
aciklama: Asama 3 CPU'ya bagli (%100, GPU %7): tek kare ffmpeg yigini + ayni dikey/bantli pencerenin film boyunca tekrar reddi; merged3 paketi
kaynak: testbench/darbogaz_1107/R_ffmpeg_cpu/RESULT.md, S_barflag/MERGE.md
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# stage3-cpu-geometri-1107

EP03 1107: 50 dikey/yan bant Flash reddi sadece 11 pencereden (biri 6 kez); ret hafizasi +-2 cekimdi. Duzeltme: geometri retleri film geneli pencere hafizasi (40/50 onlenir, DOCUMENTARY_GEOMETRY_MEMORY=0 kapatir). ffmpeg: NVDEC exact decode + tek surecte cok -ss, kareler bayt-esit, film basi ~2600 CPU-sn az; scale_cuda ve skip_loop_filter esit degil (38-44 dB), kullanma. Precheck'in 18 sn'lik pano kismi cogunlukla bekleme (pano ~2 CPU-sn); render_with_qc 4563 sn'nin 1803'u media gate. subtitle_gate/picture_fit cekim kimliginde: degistirirsen biten cekimler yeniden yapilir. Paket testbench/darbogaz_1107/merged3.
