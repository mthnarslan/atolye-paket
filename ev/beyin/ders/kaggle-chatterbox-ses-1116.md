---
tur: ders
aciklama: Duygulu anlatim: Chatterbox 0.1.7 Kaggle T4x2'de 4 isci (kaggle_vo/); yerel GPU bossa worker_local.py ~20 sn/satir (2 seed) ile sondan basa yaris
kaynak: ZeroPulse LimitClock 1116; ZeroPulse LimitClock 1116
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: ortak
---
# kaggle-chatterbox-ses-1116

LimitClock/kaggle_vo: dataset jobs.json+ref.wav+worker.py, kernel 4 isci CUDA_VISIBLE_DEVICES=s%2, duygu->exaggeration/cfg/temp, 2 seed en yakin 2.6 kelime/sn, max_new_tokens=min(1000,len*12+64). Kernel slug dataset ile ayni olursa 409. Birlestirme: lc/vo.py epNN --join.

## 2026-11-16 (claude)

Ek 16 Kas 21:50: G-Labs bitip GPU bosken yerel 3050 Ti'de ayni worker (prepare_conditionals bir kez, empty_cache) satir basi ~20 sn (2 seed, ~6 sn ses). Onceki 145 sn olcumu GPU paylasimliyken. kaggle_vo/local/worker_local.py <sh> <ns> <dataset> <out> [lim] isleri ters sirada yapar; Kaggle uzun surerse yerel sondan baslar, birlestirmede eksik satir yerelden alinir.
