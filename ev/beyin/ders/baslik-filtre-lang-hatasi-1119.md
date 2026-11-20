---
tur: ders
aciklama: fremd1118 baslik2/filtre.py lang=='de' de-DE/de-CH kanallarini atiyor; rows.json 33 yerine 23 kanal
kaynak: ytmarket_run/reports/fremd1118/danisma/BASLIK_opus.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: opus
onay: 
etiket: 
---
# baslik-filtre-lang-hatasi-1119

baslik2/filtre.py lang=='de' esitligi de-DE/de-CH gibi etiketli 10 kanal/268 videoyu dusuruyor (rows.json 23 kanal/713 video; dogrusu de* ile 33 kanal/981). Duzeltilmis sette de hicbir baslik yapisi Holm'u gecmiyor (iki parcali x1,21 p 0,097; yas duzeltmesiyle x1,14), yani 'genel kural yok' bulgusu guclenir. Holm'u gecmek icin ~x1,75 etki gerekirdi. Ozellikli videolar kanal icinde daha genc (marka 6/6) -> yas karisikligi. Dil filtresinde lang.startswith('de') kullan. Rapor: ytmarket_run/reports/fremd1118/danisma/BASLIK_opus.md, betik danisma/BASLIK_opus_olc.py.
