---
tur: ders
aciklama: Chatterbox Turbo uzak sunucuda (Oracle A1 ARM CPU) RTF 4,6-4,9: ikinci anlatim seridi olarak degmez
kaynak: landmark voice lane
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# remote-chatterbox-1106

A1 (4 OCPU ARM, 24 GB): venv py3.10 + chatterbox-tts 0.1.7 torch 2.6 CPU kuruldu, chatterbox_serve.py aynen calisti (agirliklar HF'den inen, ilk yukleme ~3 dk, RAM ~3 GB), referans yukleme 17 sn. 3 cumle (3,2-3,8 sn ses) 15,6-17,5 sn hesap = RTF 4,6/4,9/4,9. Yerel RTX 3050 Ti ~1,1x gercek zaman (RTF ~0,9), yani uzak serit yerelin ~%20'si kadar katki verir; esik 3 asildi, tam kosu baslatilmadi. VDS 4 GB RAM (9router ile 1 GB bos) modeli (~3,8 GB agirlik) tasimaz, denenmedi. Not: sunucu kodu degisiklik gerektirmez (SO_EXCLUSIVEADDRUSE ve typeperf yalniz Windows yollari). Tunel: ssh -L 17864:127.0.0.1:7864 a1. Tekrar denemek icin A1 ~/cb (venv + serve) hazir; GPU'lu uzak makine olmadan yararsiz.
