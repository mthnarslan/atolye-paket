---
tur: ders
aciklama: Parti sirasinda RAM tuketicileri (medyanlar), hyperframes ffmpeg -threads 4 (840->463 MB), MemoryGate hyperframes'i saymaz, SigLIP bellek vermez; fastrender 239a954 prod'da
kaynak: EP02-EP05 partisi
olusturma: 2026-11-05
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# ram-tuketiciler-1105

Olcum 5 Kas 20:56-21:06 (parti EP02-EP05): medyan/max ffmpeg toplam 1,2/3,9 GB; chrome-headless-shell (hyperframes) 1,6/2,5; kullanici Chrome 0,9/3,8; python 1,6/2,2; claude.exe 1,7.
- Hyperframes ffmpeg (libx264 medium) ornek basi ~840 MB; `-threads 4` ile 463 MB (HYPERFRAMES_FFMPEG_PATH shim, kart/motion kimligi degismez; `DOCUMENTARY_HF_THREADS=0` kapatir).
- MemoryGate hyperframes'i saymiyor -> 0,6-3,8 GB salinim; CUDA pencere okuma 181 MB WS ama gate 80 sayiyor. Chatterbox 7,4 GB commit ama WS 0,3 -> RAM degil pagefile.
- SigLIP bosta bosaltma Windows torch'ta bellegi geri vermiyor (~70 MB); gercek cozum kisa omurlu alt surec veya fp16 (kimlik/QA karari).
- Kart/motion tek tarayici + kareleri ffmpeg'e borulama (fastrender.mjs): prod'da 239a954'ten beri.
- Bulut: Colab/GitHub Actions ToS uygun degil.
