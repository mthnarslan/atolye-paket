---
tur: konu
aciklama: Tarih nisi + 10 Kas felaket nisi dil olcumu
kaynak: ytmarket_run/bin lang_score.py, niche_lang.py, lang_niche.py; score1105, niche1105 (11-05); ytmarket_run/reports/lang1110/disaster.json
olusturma: 2026-11-06
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# dil-pazari

Tarih nisi icin dil secimi (ytmarket_run/bin: lang_score.py, niche_lang.py, lang_hist.py, lang_niche.py; veri score1105, niche1105).

**Yontem:** agirliklar olcmeden once sabitlenir (GE-McKinsey iki eksen). Cekicilik: bosluk25 yeni-giren20 taban15 deger20 talep10 eski-icerik10; Guc: ses40 konu30 metin15 AI-tepki15 (guc ekseni cogunlukla varsayim, Ingilizce disi ses test edilmedi; deger metrigi dusuk guven). Talep ulkeden ulkeye tasinmaz, her pazarda ayri olc. CPM tablolari celisiyor -> gercek RPM yalniz kendi Studio'dan. Geriye donuk test yontemi yok; onceden yazilmis durdurma kuralli pilot.
**Niş kalibiyla olc:** genis anahtar kelime ('historia','volcan') Roblox/dram/film karistirir; 'entire/ganze/toda la historia' + 'X in N minutes' kalibini vidIQ outliers ile (son 6 ay, uzun video, <50k abone, >=100k izlenme) ara. flash-medium gercek basliklarda 240 sn'yi asar, hit temizligi icin flash-low (40 baslik/istek). Her yeni OUT klasoru onbellegi sifirlar. 5 YouTube anahtarinin kotasi tek aksamda bitti (3-4 tam kosu).

**Sonuc (kalip, 11-05):** DE en iyi: 16 video/2 kanal (Geschichte. Lebt. 18k abone 105-493k; kopyasi 1k abone 116k; RPM 2,22). EN 12 video/~10 kanal, kalabalik (RPM 3,42). ES 5/4 (Animated History Espanol = Ingilizce kanalin dil kopyasi, 10k abone 303k; RPM 1,37). IT 5/2 ve PT 3/2 ayni cok dilli operator; FR 0, JA 0.
**Nis geneli (90 gun, kucuk kanal >=100k payi):** EN %22, DE %25, ES %25, FR %10, PT orneklem kucuk; siradan kucuk-kanal videosu medyani her dilde ~100-200 izlenme (taban farki kayboldu). 100k+ videolarin genc (<=12 ay) kanal payi: pt %45, es %22, ja %19, en %10, de %9 (Almanca nis yerlesik kanallarda). Dil filtresi zayif, orneklem toplam pazar degil.
**Ceviri kanal verimi (son 10 uzun video medyani/orijinal):** Kurzgesagt ES %12, PT %8, DE %6, FR %1,3, JA %1,4; Animated History ES %7. YouTube oto-dublaj 27 dil, dublajli izlenme suresi orijinalin ~%75'i; ayri kanal vs ses izi kaynaklarda celisiyor. Chatterbox cok dilli (mtl_tts.py) denenmedi; Pocket yalniz Ingilizce.
**Risk:** Almanca kazananlar yerel sehir/bolge tarihi; SS/Gestapo konusunda Almanya'da gamali hac vb. §86a yasak, kucuk resimde kullanma. Ispanyolca izleyicinin cogu ABD olabilir.

## 2026-11-10 (claude)

2026-11-10 felaket/kaza nisi (lang_score.py disaster, reports/lang1110): A(pazar)/S(guc): ja 3.69/2.25 (orneklem 26 video, ses+metin zayif), de 3.38/3.75, es 3.24/3.75, en 2.94/4.70 BEKLE (talep 9.6M en buyuk ama yeni kanal hit payi %18, siradan video 1k+ %3, Mentour Pilot hakim), pt 2.68 (yuksek CPM ulke %33), fr 2.21, it kapi (2 kanal). DE: 7 hit 3 kanal, yeni kanal payi %43, eski icerik acigi 0.67, izleyici %100 pahali ulke; Letzte Stunden 4k abone 105 gunluk 586k; Wyngx auf Deutsch (EN kanalin ceviri kopyasi) 11k abone 475k = bu niste ceviri %1-12 kuralini curutur. Karar: ana kanal DE, uretim EN metin -> DE ses; on sart Almanca ses kor dinleme testi (Pocket sadece EN, Chatterbox cok dilli denenmedi). vidIQ kredisi 5 Ara'ya kadar bitti; vidiq.py artik hata cevaplarini onbellege yazmiyor.
