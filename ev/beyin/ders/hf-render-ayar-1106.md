---
tur: ders
aciklama: HyperFrames Case File chunk render ayari: --gpu --no-browser-gpu, workers etkisiz
kaynak: testbench/speed_1106/render
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# hf-render-ayar-1106

HyperFrames capture JPEG ekran goruntusu (34 s/24 s video) sonra sirali x264 encode (15 s). -w 1..6 neredeyse etkisiz (79->60 s) ama RAM artar. --gpu (NVENC) encode'u kisaltir, --no-browser-gpu render basina ~0,8 GB RAM tasarrufu; ikisi birlikte par 2: 123 -> 93,5 s (-24%), ~1,95 s render / 1 s video (10 dk film ~19,5 dk, eskisi ~28). mov/png-sequence 3x yavas, -q draft SSIM 0,984 (red), experimental-fast-capture kazanc yok, HF_STATIC_DEDUP=0 kotu. Render bit-bit ayni degil: baseline-baseline SSIM 0,990 (gurultu tabani). Makine paylasimli, sure +-15% oynar; par 2 -w3 varsayilan GPU ile bos RAM 0,65 GB'a dustu, par 3 de 2 GB kuralini bozar. Tavsiye: render ... -w 3 --gpu --no-browser-gpu --par 2.
