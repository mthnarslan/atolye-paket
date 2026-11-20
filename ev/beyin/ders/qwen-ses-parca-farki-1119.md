---
tur: ders
aciklama: Qwen3-TTS: 0. parca iyi/1. parca kotu = icerik (tireli kisaltma hecelemesi) ya da 0,6 sn dijital sifir durak; loudnorm+mp3 zinciri dedektor skorunu her dilde kotulestirdi; voice-clone non_streaming_mode varsayilan False
kaynak: dil_test/qwen_ayar, Opus danisman raporu 11-19
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# qwen-ses-parca-farki-1119

Opus ses danismani 11-19 (dil_test). Cumleler bagimsiz uretiliyor, durum tasinmiyor -> 'ilerledikce bozulma' degil. Adaylar: (1) FR/PT metinde 'em-pe-el-cinquante' heceleme (DE duz metin geciyor); (2) paragraf sonu 0,6 sn dijital sifir (ASVspoof dedektorleri sessizligi kisayol ogrenir, arXiv 2106.12914). DE kiyasi karisik: DE farkli (duz, kisa cumleli) metin. loudnorm+mp3 160k: DE .099->.129, FR .685->.732, JA .562->.646, KO .422->.518. Referans en buyuk etken (FR p04 4/4, p08/p12 1/4). Pocket 4.0.1'de french/german/portuguese/spanish (+_24l) var (CC-BY-4.0). ZONOS3-Mini apache-2.0 43 dil (11-09), 4 GB dogrulanmadi. OmniVoice agirlik CC-BY-NC. Tontaube int4 6,5 GB tepe.
