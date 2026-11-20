---
tur: kaynak
aciklama: YouTube Test & Compare 2026-11-19 kurallari (Inconclusive = ilk yuklenen kalir, olcut izlenme suresi payi) + az trafikte gurultu kurali: tepe pay > %33,3 + 150/kok(izlenme); tek hipotez 5 videoda birlesik oku
kaynak: ytmarket_run/reports/fremd1118/danisma/TEST_opus.md + TEST_opus_sim.py/.txt + TEST_opus_pool.py/.txt (Noch harmlos danismanligi 11-19)
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# youtube-test-compare-kurallar-1119

Resmi https://support.google.com/youtube/answer/16391400?hl=en (tarih yok, 2026-11-19 ham curl; eski answer/13861714 buraya yonleniyor): en cok 3 kol; mod yalniz baslik / yalniz kapak / baslik+kapak cifti (baslik testi 2025-12-05'ten beri herkese: https://www.searchenginejournal.com/youtube-title-a-b-testing-rolls-out-globally-to-creators/562571/); yalniz masaustu Studio, gelismis ozellik sart (https://support.google.com/youtube/answer/9890437?hl=en); test en cok 2 hafta, surerken baslik/kapak degisirse durur; kazanan olcutu izlenme suresi payi (CTR degil) + anlamlilik; Performed Same -> siz secin; Inconclusive -> ILK YUKLENEN varsayilan olur (yukleme sirasi fiili karar); kucuk kontrol grubu varsayilani gorur; Shorts/planli canli/premiyer (bitene dek) test edilemez; kol basi CTR resmi sayfada yok. Gurultu (sim, 15 dk video, sure CV 1,04, esit gosterim): esit kapaklarda tepe pay %95 olasilikla %33,3 + 150/kok(izlenme)'ye cikar (2 kolda %50 + 140/kok); 300 izlenmede 1,3x iyi kol bu esigi %30, 1200'de %81 gecer; esik gosterimle degil izlenmeyle konur. Az trafikli kanalda tek video testi kural ogretmez: ayni tek hipotezi (or. koyu vs beyaz zemin) her videoda en az 1+1 kolla tekrarla, video basi log pay oranini ters-varyansla birlestir (5 video x 300 izlenme, 1,3x: guc %92); bir video agirligin >%50'sini tasiyorsa karar verme. Video basina secimde en yuksek payi elle koymak savunulabilir (esitse kayip yok).
