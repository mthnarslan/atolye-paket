---
tur: ders
aciklama: LosslessCut hizi -c copy (kodlamasiz) sayesinde; bizim kare-tam 1080p/25 kesimde hat zaten -ss+NVENC+concat copy, kazanc cekim basina ~1 sn
kaynak: testbench/fastcut_1105/results.jsonl
olusturma: 2026-11-05
guncel: 2026-11-05
yazan: claude
onay: 
etiket: 
---
# losslesscut-kopya-kesim-1105

10 sn kopya kesim 0,69 sn/28 MB vs cekim render 5,9-6,9 sn/237 MB. Output seek (-ss -i sonrasi) 15 sn ve yanlis kare: kullanma. Kopya on-kesim + encode 0,26+4,36 sn, SSIM 0,999, film basina 3-5 dk. Darbogaz seek degil, eszamanli ffmpeg+chrome RAM'i. Olculmeyenler: scale_cuda tam GPU zinciri, tek decode cok pencere.
