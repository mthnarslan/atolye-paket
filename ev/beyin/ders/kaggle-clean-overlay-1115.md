---
tur: ders
aciklama: Kaggle T4'te clean_overlay: iş süresi yerelle aynı (125,7 vs 135,3 sn), ama tam kernel GPU kuyruğunda 55 dk bekledi; yalnız toplu/gece işine uygun
kaynak: testbench/kaggle_clean/SONUC.md, kanit/summary.txt
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# kaggle-clean-overlay-1115

2026-11-15 testbench/kaggle_clean: logo_sinav klip C işleri J1/J2 ProPainter, J3 LaMa + A/B/E ProPainter. T4 iş süreleri J1 62,5 (yerel 53,8), J2 33,8 (60,0), J3 29,4 (21,5); karşılaştırılabilir toplam 125,7 vs 135,3 sn. GPU tepe 2615 MiB, kota 0,08 sa. Uçtan uca 3974 sn: yükleme 146, kuyruk+açılış 3317 (mini kernel aynı gün hemen açılmıştı), kurulum 29, koşu 180, indirme 40. Kareler: J1 yerelle aynı temizlik, E BBC logosu gitmiş. Kod: kaggle_clean/code + yama.diff (Linux model yolları), dataset metehankahraman/clean-overlay-t4-20261115 private, Kaggle dataset'i /kaggle/input/datasets/<user>/<ad> altına açıyor. Sonuç: hız kazancı yok, kazanç yerel GPU/RAM'i boşaltmak; kuyruk yüzünden film içi değil gece toplu temizlik için.
