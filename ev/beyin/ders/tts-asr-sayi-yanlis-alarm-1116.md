---
tur: ders
aciklama: TTS satir kontrolu Whisper ile: sayi/rakam farki yanlis alarm (117->14); sayilari iki taraftan atinca gercek hata kalir; alternatif seed dosyalari once denenir
kaynak: ZeroPulse LimitClock 1116
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: ortak
---
# tts-asr-sayi-yanlis-alarm-1116

LimitClock lc/asrcheck.py (faster-whisper small.en CPU int8; GPU'da cublas64_12 yok, av.open metadata_errors hatasi -> numpy 16k girdi). Ham recall<.85: 117 satir, cogu 'thirteen'->'13'. Sayi kelimeleri+rakamlar atilinca 14; gercek bozuk 3 (kesik son, 'Normal.'->'Nogarmol', isn't->'is an'). Kaggle _s<seed>.wav alternatifleri once denenir; contraction belirsizse 'is not' yaz. 577 satirda CPU ~20 dk.
