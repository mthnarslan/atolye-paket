---
tur: ders
aciklama: Logo tespiti: clean_overlay --auto (zamansal std) yari saydam logoyu kaciriyor + gokte yanlis leke -> dev kutu, ProPainter 6+ dk; Flash 6 kare kutu (4-20 sn) dogru, clean_overlay --boxes ile temizle
kaynak: GaiaTrace EP01 HOOK 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# logo-tespit-flash-kutu-1108

GaiaTrace EP01: --detect-only MKO PHOTOGRAPHY yari saydam yaziyi kacirdi, gokte 3 yanlis leke isaretledi; kutu 400x860'a sisti, ProPainter 118 karede 6 dk'da bitmedi (GPU 3.9/4 GB). Zaman-ortalamasi-kenar sezgisi de pan cekimlerde cok yanlis pozitif verdi. Cozum: testbench/pantanal_1108/tools/logo_box.py -> 9router ag/gemini-3.8-flash-low, 6 kare tek istek, reasoning_effort minimal, box_2d 0-1000; 19 klipte 4-20 sn, MKO/BBC/kanal ikonu dogru kutu. Ayni istekte title_frames: baslik/altyazi/abone grafigi olan kareler. clean_overlay.py'a --boxes JSON eklendi (maske = kutular + grow). Not: 9router stream:false'a ragmen SSE donebiliyor, data: satirlarini birlestir.
