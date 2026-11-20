---
tur: ders
aciklama: clean_overlay --jobs: LaMa-zorla 3,6x hizli (6 kesit 191 vs 679 sn, yuk altinda) ama duz/doku zeminde leke ve dikey cizgi birakiyor; hibrit (auto) kalsin
kaynak: gaia_1108 clean_lama testi
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# lama-vs-hibrit-temizlik-1108

EP01 6 logolu kesit, asama 3 kosarken (GPU paylasimli, bos RAM 1,8 GB): auto (LaMa/ProPainter hibrit) 679 sn, force=lama 191 sn. Yan yana (testbench/gaia_1108/clean_lama/cmp.jpg): gri duz zeminde ve yaprakta LaMa leke + dikey cizgi; auto temiz. Buyuk kutu (GAIA DOCS 215x214 px, agac ustu) ikisinde de belirgin yama izi. Kesit basi ~113 sn yuk altinda -> tam filmde (~%45 kesit logolu) saatler; hiz icin temizligi asama 3 bittikten sonra bos GPU'da kos.
