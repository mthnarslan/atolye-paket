---
tur: ders
aciklama: Yari saydam logo: alfa olcup unblend + Poisson + gren BBC'de iz birakmadi; opak yazida akis doldurma sabit/dokulu cekimde yetmiyor, uretken model sart
kaynak: oturum 2026-11-08 VideoLab
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# videolab-logo-temizlik-1108

BBC (alfa 0.78, harfler bos): eski bbc_perfect_clean dolgu oynatirken capraz X cizgisi + testere lekesi biraktigi icin gorunuyordu (zaman ortalamasi |detay| haritasinda net). VideoLab/unblend_logo.py: duz karelerden L ve tek alfa regresyonu, (O-aL)/(1-a) rehberinin Gauss 1.8 alcak gecirgeni, alfa kenar bandi gradyani kesilir, cozum bolgesi logo+5px (H.264 halkasi icin; yoksa kutu cercevesi kalir), Poisson, sonra cevreye esit luma gren (0.45; kodlama greni buyutur). Olcum: ic detay 0.63 = cevre 0.63, cerceve 0.60. Bilateral rehber kotu (gurultu bloklari). 10 sn 37 sn. Opak Red Bull '#11 Philippines': VideoLab/flow_fill.py (DIS akis, maske ici akis tamamlama, en yakin acik kare) hareketli gokyuzunde iyi, sabit/orman cekimde %1-28 kapsama -> Telea lekesi. ProPainter ve E2FGVI lisansi ticari degil; LaMa Apache-2.0.
