---
tur: ders
aciklama: Kendi videomuzun ham karesi kapakta zayif: HUD/etiket, letterbox, logo, ucuz 3D; G-Labs i2i ile ayni kareden yeniden ciz
kaynak: testbench/kapak_kare/zayif_duzelt.py, hat.py
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# kapak-ham-kare-hud-1119

19 Kas kapak isi (testbench/kapak_kare): 43 kapagin goz kontrolunde ham kare kapaklar (CASE FILE yazisi, siyah bant, logo, bulanik 640x360) belirgin zayifti; G-Labs nano_banana_pro i2i (ref = ayni kare + rakip R1, istemde HUD/logo/letterbox kaldir, fotogercekci) ile 11'i duzeldi. Kalan zayiflar: soluk renk, bulanik kare, yapistirma gibi kompozit. Ayrica G-Labs kosu ortasinda gecici baglanti reddi verdi (yeniden baslatilmadi); hat.py hazir olani atladigi icin ayni komutla yeniden kosmak yetti. Sonuc: 60 kapak, 56'si siteye (ortak-atolye /kapaklar).
