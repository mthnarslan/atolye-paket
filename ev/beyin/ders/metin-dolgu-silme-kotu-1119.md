---
tur: ders
aciklama: Olgusuz konusma eklerini/kapanislari mekanik silmek (D kolu) YZ puanini dusurmedi, 4/10 metinde 20-30 puan artirdi: konusma ekleri insan sinyali
kaynak: testbench/metin_kural_1118/dil_test/kanit3/abl/dolgu.log
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# metin-dolgu-silme-kotu-1119

11-19 dolgu.py: son metnin tum cumleleri olgu|dolgu|kapanis etiketlendi, dolgu+kapanis (en fazla 1/3) silindi, 6x HAKEM. son->D: ES_1 23->22, ES_2 22->22, PT_1 17->23.5, PT_2 22->23.5, FR_1 57->68.5, FR_2 22->43.5, JA_1 26.5->50, JA_2 30->42, KO_1 26.5->23.5, KO_2 23->55. Hedefli silme (yalniz hakemin yz>=50 kosuda alintiladigi cumle, sil.py) ise isliyordu; genel silme ritmi bozup ansiklopedik yapiyor. Kural: yalniz hakemin alintiladigi cumleyi sil, toplu dolgu temizligi yapma.
