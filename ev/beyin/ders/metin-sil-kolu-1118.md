---
tur: ders
aciklama: YZ hakemi isaretli kopru/ozet/vecize cumleyi YENIDEN YAZMA, SIL: JA 78->25, KO 72->28, FR 78->42; yeniden yazma yeni kalip uretir
kaynak: kanit3/abl/sil.log, hedefli.log, hepsi.log
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# metin-sil-kolu-1118

testbench/metin_kural_1118/dil_test/sil.py. Hakem (hydrogen) yz>=50 kosularda alintiladigi cumleler: model yalniz 'tablodan olgu tasiyor mu' der, tasimayan (kopru, ozet kapanis, retorik soru, vecize) Python ile silinir. 3 kosu ortanca: JA_1 A78 H28 R65 S25; KO_1 A72 H78 R72 S28; FR_1 A78 H78 R78 S42. H=hedefli yeniden yazim (KO'da 'hanaissik salpyeobogetseumnida', 'ireoke...' gibi yeni kopru/ozet ekledi). R=rastgele cumle kontrolu. Ayrica ablasyon: yasak listesi kaldirilip yalniz insan ornegiyle yazim 78-92 (v3 22-24) -> yasaklar ise yariyor. Hakem insan metnine ort 10-15 verir (n=8/dil; JA 2 insan metnine 72/88).
