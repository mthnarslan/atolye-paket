---
tur: ders
aciklama: Dublaj, konusmacinin kendi Ingilizce sesinden klon: ~%15 ada Ingilizce aksanla okunur; o klonla uretilmis temiz Turkce adayi ref yapinca 50->8; hizli Ingilizce ref icin konusmaci basi sabit OmniVoice speed
kaynak: testbench/dub_1107 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# dub-ingilizce-ref-aksan-1108

testbench/dub_1107 (65 dk Colin&Samir + 68 dk Sweat Equity). 1) Ingilizce podcast ref'i ile OmniVoice Turkcede 7,1-8,4 hece/sn konusur (slot 6,0'a gore fit 0,66-0,86) -> konusmaci basi SABIT speed = 6,6/olculen (0,78-0,98; satir basi degil). 2) Ingilizce ref'te adalarin ~%15'i Ingilizce aksanla/anlamsiz cikar (Whisper dil=en, 'thank you for watching' halusinasyonu); reseed duzeltmez (45->36->28). Cozum: ayni klonla uretilmis, backcheck hatasi en dusuk 8-14 sn Turkce adayi ref yap (spkT, speed yok) -> 50 kotu adadan 8 kaldi, kalanlar sayi okuma farki. Ikinci videoda bastan: 12 ada/konusmaci prob -> spkT -> tam uretim. Backcheck olcusu max(kelime hatasi, 1-P(tr)). 3) OceanAPI 'The request is invalid' bazi tam metinlerde deterministik ('Mr. Beast, sports competitions...' -> 'MrBeast' gecer); tek ada + kucuk metin varyantlariyla doldur (src/fill_tr.py), kalan 1-2'yi Claude yazar. 4) Post-TTS refit 2 tur: 1. tur gecikmeyi artirdi (late>1s 20->41), 2. tur sadece >1,03/<0,8 -> 3, max 2,5 sn. Zincir: src/run_tail.sh.
