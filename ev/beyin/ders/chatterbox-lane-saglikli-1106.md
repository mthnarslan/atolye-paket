---
tur: ders
aciklama: Chatterbox Jeff hatti saglik olcumu: 32 tok/s, tasma yok; kalan hiz kisiti token dongusu (GPU %37, launch-bound)
kaynak: landmark ses hatti hiz arastirmasi 1106
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# chatterbox-lane-saglikli-1106

2026-11-06 landmark ses hatti: sunucu pid dedicated 3327 MB, shared 78 MB (saglikli), lm_voice logu audio/wall ~1.2-1.4 = ~32 tok/s (saglikli 34.8). Chrome/Antigravity GPU surecleri toplam <100 MB dedicated. GPU kullanimi %37: t3.inference_turbo tek tek token donguyle CPU/launch-bound (her adimda torch.all sync + tqdm). Hizlanma adaylari (fp16, CUDA graph/static cache) 4 GB kartta ikinci model kopyasiyla test edilemez, sunucu yeniden baslatma gerektirir; olculmedi.
