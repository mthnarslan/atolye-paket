---
tur: ders
aciklama: Kaggle T4x2'de Blender 5.3 Cycles: 1080p 48spp ~5,5 sn/kare, kurulum ~40 sn, shot basi ~60 sn acilis
kaynak: testbench/recon_1113/real
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# kaggle-blender-cycles-1113

Ana hesap metehankahraman (KAGGLE_API_TOKEN=~/.kaggle_mk/access_token). machine_shape NvidiaTeslaT4 -> T4x2 OPTIX. Blender linux tar download.blender.org'dan wget (200). Poly Haven API urllib'e 403 verir, curl kullan. Olcum: A64 5,5 sn, D62 8,5 sn, ilk kare 11 sn. En fazla 2 esz. GPU oturumu: shotlari 2 cekirdege bol, STEP=2 + ffmpeg minterpolate. Araclar testbench/recon_1113/real/make_kernel.py + kpoll.sh (bekci altinda Git Bash ile).
