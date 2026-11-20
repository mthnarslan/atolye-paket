---
tur: ders
aciklama: Belgesel profil (wildlife) film klasorundeki film_settings.json'dan OKUNMAZ; CodexOutputs/<film>/film_settings.json ya da drive.py 4. arg
kaynak: oturum 2026-11-08 Pantanal
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# film-profil-yeri-1108

GaiaTrace EP01: film klasorune film_settings.json {profile:wildlife} koydum, drive.py profilsiz calisti; asama 3 varsayilan karisimla (VIDEO 40, 3D/CARD/MOTION) basladi. Kopru _film_profile engine.voice_output_dir(folder)/film_settings.json okur (CodexOutputs/<film>). Cozum: drive.py <film> 1 4 wildlife ile ilk asamadan ver; yanlis basladiysa kopruyu durdur, 03_materials'i yedekle, CodexOutputs/<film>/film_settings.json yaz, asama 3'u profille yeniden kos. Kontrol: 03_materials/settings.json profile alani ve events'te targets VIDEO 100.
