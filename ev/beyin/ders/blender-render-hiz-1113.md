---
tur: ders
aciklama: Blender EEVEE video hizi: golge en pahali, motion blur 3x, hacim toz kareli bozulur; STEP=2+minterpolate, 720p, 2 serit
kaynak: testbench/recon_1113/scene.py, lane.sh, assemble.py; testbench/recon_1113
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# blender-render-hiz-1113

Recon tarzi 1 dk Ever Given (testbench/recon_1113). Olcum (RTX 3050 Ti, GPU baska oturumun chatterbox TTS'iyle %100 paylasimli, 87C): %25 cozunurlukte golge ACIK 5-15 sn/kare, KAPALI ~2 sn. Motion blur sureyi ~3x yapar (kapattik). Hacimsel 4D gurultu toz kutusu kareli/capraz desen verdi -> kaldirildi, kum firtinasi ffmpeg 2B katman (bulanik gurultu kaydirilip alphamerge). Hizlandirma: arazi/su/pus/yol golge atmaz (visible_shadow=False), 1280x720 + 8 TAA ornek, STEP=2 (tek kareler 12.5 fps) + ffmpeg minterpolate mci/aobmc ile 25 fps (gozle temiz, kamera hareketi yavas), 2 paralel Blender seridi (~13 sn/kare/serit paylasimli GPU'da). Seridi bekci altinda Git Bash ile kos ('C:/Program Files/Git/bin/bash.exe'; duz bash WSL'e gider). Kartlar/harita 3 paralel GPT iscisine (~9 dk). Sonraki kaldirac: GPU'yu bos zamanda kullan (TTS sunuculari kapaliyken), 960x540+upscale.

## 2026-11-13 (claude)

Ek (18:10): (1) Blender ciktisini grep'e borulayinca grep tamponluyor, log sahne bitene kadar sessiz -> bekci 10 dk'da yanlis TAKILDI der; grep --line-buffered kullan ya da stall-min'i sahne suresinin ustune koy. (2) Bos RAM 0,3 GB'a dusunce (baska oturumun python+ffmpeg'i) kare suresi 13 -> 104 sn oldu: takas. Iki Blender'i birden kosturma, tek seride dus. (3) minterpolate cikti N kareden ~0,1 s kisa; tpad ise yaramadi -> ses yerlesimini olculen parca sureleriyle yap (assemble.py REAL). Sonuc: 58,8 s 1080p, -15,9 LUFS; toplam render ~60 dk paylasimli GPU'da.
