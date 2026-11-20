---
tur: ders
aciklama: Referans videodan ornek: kesit alma, sifirdan uret; sahne 3-7 sn, kesim yalniz cumle sinirinda; SFX animasyon anahtar karesine
kaynak: oturum 2026-11-11 asker ornek
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# asker-ornek-sifirdan-1111

Kullanici 11-11: referans videodan kesit alip araya 1-2 sn ekleme yapmak reddedildi (animasyonu boluyor, cok kisa). Dogru yol: referans yalniz stil; animasyonu HyperFrames'te sifirdan yaz (hf/asker1/tools/build.py: edge-tts kelime zamanlari -> her vurgu kelimesine sabit tween, sahne degisimi yalniz cumle sinirinda, sahne 3-7 sn, gercek foto/kesit bolum sinirinda 3.5-4.5 sn). SFX: animasyon zamanlari bilindigi icin cue = tween zamani, mix.py onset/tepe hizalar (dinlemeden tam senkron). Teçhizat gorselleri G-Labs nano_banana_pro siyah fon (~45 sn/adet, 3 paralel), kenara bagli koyu bilesen -> alfa (tools/key.py). Not: bekci.py ile Windows'ta npm CLI calistirirken .cmd tam yolu ver (hyperframes.cmd), yoksa WinError 2.
