---
tur: ders
aciklama: ZP render 1 vs 3 NVENC paralel: ortalama 2360 vs 2276 sn (fark gurultu icinde), bos RAM 1-361 MB; kalite esit. Paralel render kazanc kanitlanmadi
kaynak: testbench/zp_render_1118/kalite.txt, runs/*_kos.out
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# zp-paralel-render-1118

testbench/zp_render_1118/runs: A=sirali (1 enc) 2165,6 / 2555,1 sn; B=3 paralel 2952,2 / 1600,2 sn. Kosu ici sapma farktan buyuk. min bos RAM A1 1 MB, B 190/361 MB. SSIM >=0,9995, ses md5 esit. Sonuc: RAM tavanda, paralel render prod'a alinmaz; once RAM (32 GB) ya da Chrome sayisi.
