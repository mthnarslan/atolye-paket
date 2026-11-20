---
tur: ders
aciklama: Metin yazimi 8 dil: istemdeki kural tablo disi iddia (10/10) ve ozet kapanisi (9/10) onlemiyor; yazim sonrasi ortak/metin_denetle.py + TTS dinleme sart
kaynak: testbench/metin_kural_1118/dil_test/SONUC.md; dil_arastirma2.md; ortak-site/public/nasil/metin/METIN_REHBERI.md
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# metin-denetim-8dil-1118

18 Kas testi (testbench/metin_kural_1118/dil_test/SONUC.md): ayni istem + bilgi tablosu, EN/TR/DE/ES/PT/FR/JA/KO. Her dilde model tablo disi gerekce ekledi (pil gerektirmez, yuruyuste fark eder, arac ici) ve ozetle kapatti. Ritim CV insan cevirisinden dusuk (PT 0,27-0,31 vs 0,48); ES ayrismiyor (esik yok). JA YZ 31/31 desu/masu, insan anlatici da/dearu -> hitap kanal profilinde secilir. KO 합니다 %95. --dilbilgisi aday listesi: FR cinsiyet 2/2, DE Karabiner 2/2; ES creada 0/2, JA 特注 0/2, KO kod okunusu uyduruyor; FR '1,4 kilo' tekil dogru (cogul 2'den). Regresyon: insan 31 metnin 3'unde uyari, ucu de gercek (insan cevirmen de ozetle kapatiyor -> kapanis alarm, karar degil). Sure kelimeyle olculmez (PT 335-451 kelime, KO 230-242): TTS saniyesi. Arastirma dil_arastirma2.md: olculmus AI kalip verisi yalniz KO (patina/im-not-ai, Tem 2026); ES/FR/PT/JA listeleri olcumsuz.
