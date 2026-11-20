---
tur: ders
aciklama: Pocket TTS hizlandirma olcumu: sunucu LOCK'lu, tek sunucuda eszamanlilik fayda vermez; 2 worker +%30
kaynak: testbench/speed_1106/voice
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# pocket-hiz-1106

Olcum (20 chunk, 264 s ses, yuklu makine): tek worker 2 thread 3,03x gercek zaman, 3,4 GB. Ayni sunucuya 4 esik istek 2,77x (pocket_serve.py LOCK'u siraya dizer). POCKET_THREADS 1=2,32x, 4=3,02x (CPU 2 kat), 8=2,05x ve 5,7 GB: 2 optimum, degistirmek chunk onbellek anahtarini (service_info) bozar. 2 worker x 2 thread, istekler bolunmus: 3,95x (+%30), ses bayt-bayt ayni, WER/tekrar/loudness (-16,5 dBFS) ayni, ama +2,3 GB RAM; RAM yuklu makinede 2 worker iki kez cokme korumasina takildi. 10 dk film (~600 s ses) 198 s -> ~152 s (~45 s kazanc). Oneri: tek worker kalsin; kazanc icin generate_full_voiceover 2 chunk/2 port olmali (prod degisikligi, RAM>6 GB iken). Quantize/adim azaltma ses degistirir, denenmedi.
