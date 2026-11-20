---
tur: ders
aciklama: Kısa/tepeli Chatterbox sesinde tek geçiş loudnorm -17.7 LUFS bırakıyor (denetim -16±1.5 FAIL); voice_engine._settle_loudness ikinci geçişle -16.0'a çekiyor
kaynak: oturum 6 Kas
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# kisa-ses-loudnorm-sapmasi

MINI_1106 1. aşama FAIL: loudnorm -25.9→-17.7. Denetim gevşetilmedi; documentary_voice_engine.py _settle_loudness (0.5 LU üstü sapmada volume+alimiter 0.84) eklendi, commit 0ef6cea. Sonuç -16.0 LUFS, tepe -2.8 dBFS.
