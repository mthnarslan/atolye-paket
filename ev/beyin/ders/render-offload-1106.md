---
tur: ders
aciklama: render_with_qc sunuculara (a1/VDS) tasimak kaybettirir; sure cogu Flash precheck + gate bekleyisi, israf reddedilen 3D Chrome renderlari
kaynak: Engineered batch 1106, alt ajan olcumu
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# render-offload-1106

Olcum 1106 (testbench/render_offload_1106/FINDINGS.md): NVENC kesim 0,6 sn yerelde; a1 gidis-donus ~10 sn, VDS ~21 sn (upload 3,5/1,7 MB/s, NVENC yok) -> offload yapma. render_with_qc zamaninin %40-55'i icindeki Flash precheck (runner.py _prerender_precheck), %5-16 gate bekleyisi, ~%35-40 ffmpeg/chrome. Reddedilen VIDEO kesimi ~5 sn (film basi 3-9 dk toplam) -> onemsiz. Asil israf reddedilen 3D Chrome render ~19 sn (EP03 76 adet ~24 dk). Oneri: 3D icin render oncesi ucuz kapi + ilk adayi iyilestirme (grid_prefilter siralamasi + pillarbox/yan bant/diyagram ret siniflarini hatirlama).
