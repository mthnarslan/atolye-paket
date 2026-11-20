---
tur: ders
aciklama: gemweb: 10 hesabin hepsi Google 1095 hatasiyla ayni anda dinlenmeye girebiliyor; istekler 300 sn ReadTimeout, kota bitmis degil
kaynak: testbench/doc_ab_1118/out/B1
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# gemweb-1095-toplu-dinlenme-1119

11-19 03:10-03:22: /durum'da 10/10 hesap 'dinleniyor', son_hata 'Unknown API error code: 1095' (Google gecici). 5s kullanim %7-84, kota sorunu degil. Belgesel B1 S1 ses hakemi 8/9 istek 260-300 sn EXC -> REVIEW, film durdu. Uzun koşu oncesi/sirasinda curl :8790/durum ile hesap durumuna bak; hepsi dinleniyorsa kosuyu baslatma, acilmasini bekle. Hiz olcumu bu pencerede gecersiz.
