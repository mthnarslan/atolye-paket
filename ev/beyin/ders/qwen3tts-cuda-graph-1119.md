---
tur: ders
aciklama: Qwen3-TTS 0.6B Windows'ta faster-qwen3-tts 0.3.2 (CUDA graph, bf16) ile 8,2x hizli: RTF 6,27->0,76; fp16 coker
kaynak: qwen_hiz ajan 11-19
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# qwen3tts-cuda-graph-1119

Taban qwen_ses.py 6 cumle 284,7 sn uretim / 45,4 sn ses (0,16x), VRAM 2,7 GB. faster-qwen3-tts 0.3.2 --no-deps (0.4+ transformers>=5 ister): 33,6 sn, VRAM 2,9 GB, +~60 sn bir kerelik yukleme/graf isinma. Kalite dagilimi ayni (sure/RMS/dedektor), kulak kontrolu yapilmadi. fp16 device-side assert. Sebep Windows kernel baslatma yuku (GPU %9). Ayrinti testbench/metin_kural_1118/dil_test/qwen_hiz/RAPOR.md
