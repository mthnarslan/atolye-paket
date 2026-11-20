---
tur: ders
aciklama: Kaggle ses kernel: wheel+agirlik onbellek dataseti kurulum 217->100 sn, kernel 453->298 sn, kalite ayni; agirligi /kaggle/input'tan dogrudan okuma yavaslatir, yerel diske kopyala; cikti kernel bitmeden inmez
kaynak: testbench/kaggle_vo_hiz_1118
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# kaggle-vo-envcache-1119

testbench/kaggle_vo_hiz_1118 RAPOR.md. INSTALL 217 s (eski, ayni gun) / 444 (1116) -> 100 s (offline wheel, --no-index --no-deps, 4 paralel pip). Agirlik mount'tan from_pretrained 4 isciyle 648-740 sn (kotu), yerel diske kopya 298 sn. kaggle kernels output kosarken bos doner: bolum sirali EPxx.done tek kernelde yalniz kernel bitince iner. Bolum basina kernel ilk bolum 323 sn (eski 559) ama sabit ~290 sn ek yuk. Kalite 24 satir whisper eslesme 0.919/11 birebir, LUFS ayni. Ayni slug dataset+kernel 409 verir.
