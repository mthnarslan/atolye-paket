---
tur: ders
aciklama: Blender 5.3 portable ile video icin 3D sahne: EEVEE ~2 sn/kare, hacim duman, x-ray, HyperFrames'e iz JSON
kaynak: asker4 Javelin vs T-72, 2026-11-13
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# blender-3d-video-1113

Kurulum: C:/Users/meteh/tools/blender/blender-5.3.0-windows-x64/blender.exe, headless 'blender.exe -b -P scene.py -- args'. Ornek: hf/asker4/blender/scene.py + run_all.py (5 cekim, 922 kare ~25 dk, RTX 3050 Ti). EEVEE + AgX, 40 ornek ~2 sn/kare. Duman/ates: kup + Principled Volume, yogunluk = 4D noise (W animasyonlu) x Object koordinatindan radyal sonum; low-poly kaya ve tup iz kotu gorunur. X-ray: Principled ile LayerWeight facing->Emission/Transparent Mix, faktor 0->0.93, BLENDED. glTF tankin onu: namlu cikintisi tarafi +X; tavan noktasi icin anten yuzunden merkez yakini z'nin %80'lik dilimi. world_to_camera_view ile adli noktalarin kare basi ekran pikseli out/<cekim>_track.json -> HyperFrames'te GSAP keyframes ile 3D'ye kilitli etiket. Dikkat: iz takip eden elemana x/y'li giris animasyonu verme (konumu 0,0'a ceker), sadece opacity. bekci: subprocess ciktisi cekim sonunda toplu dustugu icin --stall-min 30 kullan; bekci icinde 'bash -c' WSL'e gider, dogrudan exe cagir.
