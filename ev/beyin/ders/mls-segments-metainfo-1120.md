---
tur: ders
aciklama: MLS konusmaci/cinsiyet/kesit listesi icin rows API yerine HF repo dosyalari
kaynak: 
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: sonnet-ses
onay: 
etiket: 
---
# mls-segments-metainfo-1120

datasets-server rows API fr/es/pt train'de 502 ve cok yavas (en fazla 100 satir opus decode). Bunun yerine huggingface.co/datasets/facebook/multilingual_librispeech/resolve/main/data/mls_<dil>/metainfo.txt (SPEAKER|GENDER|PARTITION|MINUTES) ve train/segments.txt (id, archive url, begin, end) saniyeler icinde iner; gercek cinsiyet etiketi de var. Opus vs mp3 DF testi (10 AT fr/es): mp3 4/10, opus 3/10 gecti, opus daha iyi degil. fr train konusmaci basi TUT ~%3-8, pt havuzu 42 konusmacida biter (9 TUT). Arac: testbench/ses_dene/librivox/tools/rounds.py
