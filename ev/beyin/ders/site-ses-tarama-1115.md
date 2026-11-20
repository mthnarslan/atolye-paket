---
tur: ders
aciklama: Site 80 ses taramasi: 4 bozuk kart (podcast intro muzigi/canli yayin); UTMOS Ingilizce disinda ve sessiz temiz dosyada yaniltici
kaynak: oturum 238b861c 2026-11-15
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# site-ses-tarama-1115

kulak_1115/tarama.py + par.py (5 paralel CPU whisper small int8, cpu_threads=3; 62 ses 6 dk, tek kol ~55 dk). faster-whisper cuda'da cublas64_12.dll yok -> CPU. Bozuk: ispanyolca 11 (spanish_10 caz), almanca 16 (german_15 elektronik muzik), portekizce 16 (portuguese_15 1:26'ya kadar rock), ispanyolca 13 (spanish_12 canli yayin, crosstalk, klonlanacak 15 sn yok). Sebep: toplayici podcastin ilk 100 sn'sini aliyor = intro muzigi. UTMOS dil medyanlari: en 2.98, de 2.48, fr 2.31, es 1.95, pt 1.93 -> Ingilizce disinda esik kullanma; portuguese_15 temiz versiyon cogu sessiz oldugu icin 3.13 aldi. bekci.py -- bash ... WSL bash'e gidiyor: python sarmalayici kullan. subprocess ciktisinda encoding=utf-8 errors=replace + PYTHONIOENCODING.
