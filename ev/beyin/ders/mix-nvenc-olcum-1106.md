---
tur: ders
aciklama: scenefile mix NVENC p6 VBR 5M: x264'ten 17 kat hizli, yarim boyut, ayni SSIM/PSNR
kaynak: testbench/offload_1106/local/bench.log; testbench/offload_1106/local
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# mix-nvenc-olcum-1106

Ayni 1 parca (EP02 hf_01) grain'li mix: libx264 medium crf19 102.6 sn/637 MB RAM/67 MB; trim 154 sn SSIM 0.976; luma-only grain 106 sn 0.975; -tune grain 171 sn 0.953 ve 4x buyuk (kullanma); h264_nvenc 7.2 sn 460 MB RAM 118 MB SSIM 0.972. Film basina mix ~1500 sn -> ~110 sn beklenir. Teslimde NVENC'e gecmeden once tam filmde goz kontrolu + bitrate tavani (boyut icin) gerekir.

## 2026-11-06 (claude)

Duzeltme: ilk bench SSIM'i grain'siz kaynaga karsi olctu (yaniltici; grain'i silen kodlayici yuksek cikar). Adil olcum grain'li kayipsiz referansa karsi: x264 medium crf19 243 sn 131 MB SSIM 0.938 PSNR 41.35; h264_nvenc p6 hq vbr 5M max 7M 14 sn 70 MB SSIM 0.938 PSNR 41.07; cq21 167 MB (grain'de cq sisirir, bitrate sinirla). Yakin plan kareler gozle ayni. sf.py mix --nvenc (hata olursa x264'e duser).
