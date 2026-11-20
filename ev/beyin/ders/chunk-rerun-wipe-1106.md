---
tur: ders
aciklama: Parca render yeniden kosusunda build_chunk klasoru silip bitmis out.mp4'leri yok ediyordu (crater 19/24 parca kayip)
kaynak: landmark 5 film kosusu 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# chunk-rerun-wipe-1106

testbench/landmark render/lm_render.py: main() once tum chunk klasorlerini build_chunk ile yeniden kuruyor (safe_rmtree), sonra out_ok ile 'already rendered' bakiyordu -> skip hic calismiyordu; --from render yeniden kosusu tum filmi bastan render etti (~40 dk kayip). Cozum: build_chunk silmeden once out.mp4'u ck_NN.out.mp4'e tasir, klasoru kurunca geri koyar; out_ok kare sayisiyla dogrular. Ders: 'yeniden kullanir' iddiasini kod yolunda (temizlik -> kontrol sirasi) dogrula, dry-run + sahte dosya ile 10 sn'de test edilir.
