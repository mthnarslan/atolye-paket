---
tur: ders
aciklama: Blender 3D yol haritasi: EEVEE golgesiz 720p ~0,25 sn/kare; AgX emisyon sarisini kreme soldurur -> Standard; bloom ffmpeg gblur+screen
kaynak: isaac2 v3 2026-11-13
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# blender-yol-haritasi-1113

hf/isaac2/blender/road.py (K DUR OUTDIR W H): siyah zemin, emisyonlu sari bezier tup yol, ROUND N kaideleri, kamera tura ucar, DOF f/1.2, motion blur 0.5. 1280x720 28-34 kare ~10 sn (RTX 3050 Ti paylasimli). AgX gorunumu emisyon 2-6'da sariyi krem/beyaza cevirdi; view_transform Standard + emisyon ~1 dogru doygun sari. Bloom: ffmpeg split, gblur sigma 22, blend screen 0.6. Yol son turda bitiyorsa egriyi ileri uzat. GPT iscisi test karesini 'tamamen siyah' sandi (degildi): kareye kendin bak.
