---
tur: ders
aciklama: Referans videoyu taklitte eksik kalmasin: 5 sn arali 5x5 zaman damgali kare izgarasi -> gemweb envanter + bizim izgarayla fark listesi (~1 dk, 5 istek)
kaynak: Ornek_ZIPO/inv.py, gemini_envanter.md
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# gemini-video-envanter-1118

HAI tarzi ornek videoda ilk surumde yuzsuz sunucu karakteri, gercek B-roll, Wikipedia alinti karti (sari vurgu), blur/whip gecisleri, vinyet ve kaynak etiketi eksikti; Gemini fark raporu hepsini yakaladi. Yol: ffmpeg fps=1/5,tile=5x5 + drawtext pts; gemweb.sor ile her izgaraya envanter istemi + kaynak2+bizim1 izgara ile 'eksik ne' istemi. Ayrica: B-roll secerken arac tipini dogrula (Lausanne-Flon balastli ray = LEB, M2 lastik tekerlekli).
