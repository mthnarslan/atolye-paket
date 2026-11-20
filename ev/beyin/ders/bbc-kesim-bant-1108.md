---
tur: ders
aciklama: Asama 3 library_windows 5 filmde 30-40 dk/film: darbogaz archive.org baglanti basi ~1 MB/s, NVENC degil (encoder %0)
kaynak: gaia_1108 events.jsonl + Get-NetAdapterStatistics + nvidia-smi
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# bbc-kesim-bant-1108

2026-11-08 GaiaTrace 5 tam film (316 cekim/film, 4 sn siniri yuzunden ~%50 fazla): library_windows EP04 2412 sn/127 pencere, EP02 1769 sn/96. Olcum: 8 archive.org ffmpeg toplam 7,8 MB/s, NVENC encoder %0, ayni anda Cloudflare tek akis 15 MB/s -> hat bos, archive.org akis basina sinirli. 10 dk'da 114 pencere/4,6 GB. Hiz dugmesi DOCUMENTARY_BBC_CUTS (bbc_library.py _CUT_SLOTS, modul global; kopru yeniden baslamadan degismez). RAM yeterliyse (her NVENC ~400 MB) sonraki partide 12-16 dene; parti ortasinda kopru restarti asama 3'u oldurur, degmez.
