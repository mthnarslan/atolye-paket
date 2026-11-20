---
tur: ders
aciklama: Dublaj MP4 Windows Media Player'da acilmadi: YouTube kaynagi AV1, mix -c:v copy ile tasidi; h264_nvenc'e cevir
kaynak: dub_1107 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# dub-av1-oynatma-1108

yt-dlp bv*[height<=720] AV1 secebiliyor. Teslim dosyasi H.264 olmali: ffmpeg -c:v h264_nvenc -preset p5 -cq 23 -pix_fmt yuv420p -c:a copy. testbench/dub_1107/src/mix.py artik h264_nvenc ile kodluyor.
