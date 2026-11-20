---
tur: ders
aciklama: HyperFrames Windows'ta Chrome probe Intel iGPU seciyor; --force_high_performance_gpu ile RTX 3050 Ti; mini %27 hizli + RAM ferah, tam bolumde temiz olcum yok
kaynak: ana oturum 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# hf-nvidia-zorla-1118

testbench/hf_nvidia_1118: hyperframes 0.8.181 probe renderer Intel UHD (ANGLE D3D11) -> iGPU sistem RAM'i paylasiyor, min bos RAM 0,23-0,38 GB. Chrome'a --force_high_performance_gpu verince NVIDIA RTX 3050 Ti; dis bayrak yolu yok (env/config yok), testbench kopyasinda chunk-YPBIAONI.js'e env'den bayrak okuyan 2 satir yama. Mini ep06 25 sn x2: A 64,7 ort / B 47,2 ort (%27), capture 43-54 -> 33,5 sn, min bos RAM 1,4-3,3 GB, SSIM 0,9968 ses md5 ayni. fast-capture Windows'ta fayda yok. Tam bolum: baska oturumun TTS'i GPU'yu %99 tuttugu icin kirli (A 742/1844 sn). Ders: ayni makinede GPU/RAM paylasirken A/B olcumu anlamsiz; uzak makine ya da bos makine kapisi sart.
