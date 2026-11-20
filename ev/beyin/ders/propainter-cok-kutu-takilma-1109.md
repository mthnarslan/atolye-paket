---
tur: ders
aciklama: clean_overlay --jobs: cok kutulu (tam genislik serit) ProPainter isi 4 GB kartta 55+ dk takildi ve GPU kilidini tum filmlere kapatti; cozum: kilidi kap, jobs json'da o isi force=lama yap
kaynak: Gaia 1109 oturumu
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# propainter-cok-kutu-takilma-1109

2026-11-09 EP02 cekim 0168 (2,56 sn, 4 kutu: ust bant, sag kenar seridi, sol alt kose, alt tam genislik serit) clean_overlay ProPainter'da (RAFT corr) 55 dk kaldi; diger isler 20-60 sn. GPU %100, 3,7/4 GB (tasma). gaia_finish GPU kilidi tek temizlik -> EP05 07:10'dan beri bekledi. Ayni isi CPU'da LaMa: olmaz, LaMa modeli CUDA'ya kayitli (CUDA_VISIBLE_DEVICES='' -> deserialize hatasi). Cozum: testbench/gaia_1108/manual0168/hold_and_patch.py kilidi 0,02 sn yoklamayla kapar, takili clean_overlay oldurulur, gaia_finish sonraki turda need listesini clean_jobs_auto.json'a yazar (kilitten ONCE), betik o isi force=lama yapip kilidi birakir. Kalici cozum adayi: clean_overlay'de is basina sure siniri/ProPainter yerine lama dususu veya cok kutulu islerde lama varsayilani.
