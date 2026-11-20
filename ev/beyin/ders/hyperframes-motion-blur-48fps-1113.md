---
tur: ders
aciklama: HyperFrames 0.8.181'de motion blur bayragi yok; 48 fps render + ffmpeg tmix=frames=2,fps=24 ile gercek bulaniklik ve 24p
kaynak: hf/asker6 2026-11-13
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# hyperframes-motion-blur-48fps-1113

hyperframes render -f 48 sonra ffmpeg -vf tmix=frames=2,fps=24. Pocket TTS kelime zamani vermez; kelime anini satirdaki karakter konumundan tahmin et (asker6 build.py wt()). Kamera dunyasinda masa zemini kamera gorus alanindan genis olmali (kenar bosluk gorunur); ekran ustu yazilar sahne bitince gizlenmeli, yoksa filmin sonuna kadar kalir (asker6 snap1'de yakalandi).
