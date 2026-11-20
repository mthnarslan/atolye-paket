---
tur: ders
aciklama: 4 GB'ta ucretsiz Almanca TTS DF Arena'yi gecemiyor: Qwen3 0.6B en iyi p13 t1.1 ort 0.45 (39 pencere, 0'i insan p90 altinda); Chatterbox ~1, Seed-VC 0.999 (kotulestirir)
kaynak: testbench/ses_dene/RAPOR.md, skor_t2.json
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# almanca-tts-dfarena-1119

ses_dene Tur1+2 (11-19). Insan DE p90 esigi 0.00019. Qwen3-TTS-12Hz-0.6B-Base temp1.1 top_k100: p07 5 tohum 16 pencere ort .596 (%38 <.5), p13 3 tohum ort .449, p03 .862; WER .01-.09. Tohum/ayar taramasi yapisal olarak gecirmiyor. Seed-VC (VoxENES'te en zor yakalanan) DF Arena+Almancada 0.52->0.999. CosyVoice3 0.5B: ag 0.5-1 MB/s, 40 dk'da kurulmadi, wetext Windows'ta kurulmadi. Kalan yollar: buyuk model (Qwen3 1.7B, VoxCPM2 ~8 GB) ucretsiz bulut GPU'da ya da insan anlatici.
