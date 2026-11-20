---
tur: ders
aciklama: HyperFrames render: --no-browser-gpu kaldirinca %35 hizli (20 sn test 59.8->38.9 sn), -w 3/5 ve fast-capture farksiz
kaynak: hf/army/speed log_A..E
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# hf-browser-gpu-hiz-1118

hyperframes 0.8.181, 1080p30 20 sn test: A -w3 --no-browser-gpu 59.8 s; B +fast-capture 57.1; C -w5 53.3; D -w5 fast 48.5; E -w4 tarayici GPU acik (hardware gpu) 38.9 s, capture 28.6 vs 43.3, encode 5.8 vs 10.9. PSNR A-E 49 dB (ayni goruntu). Darbogaz screenshot capture; isci sayisi az etkiler. RTX 3050 Ti, ayni anda baska render varken olculdu.
