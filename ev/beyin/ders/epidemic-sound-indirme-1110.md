---
tur: ders
aciklama: Epidemic Sound: lisansli WAV toplu indirme yolu (uygulama tarayicisi, oturum acik) + SFX miks kurali
kaynak: LIMIT CLOCK v3 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# epidemic-sound-indirme-1110

Arama: sayfa icinden fetch /json/search/sfx/?order=desc&page=1&sort=relevance&term=... (muzik: /json/search/tracks/); r.entities.tracks[] -> title, kosmosId (UUID). Indirme: fetch /download/?bundle=false&context=MODAL_MUSIC_DOWNLOAD&downloadId=<uuid>&is_sfx=true|false&qualityType=lossless&sound_id=<kosmosId>&stemType=full&uiOrigin=tracklist_menu_button -> JSON assetUrl (imzali WAV, ~5 dk gecerli; remainingDownloads kotayi gosterir). Sayfa CSP'si localhost'a POST'u engeller; URL'leri JS sonucundan alip hemen dosyaya yaz + curl (limit_clock_ornek/tools/es_get.py). Tarayici panelinden Download butonu dosyayi Downloads'a dusurmuyor. SFX 96-192 kHz gelir -> resample_poly ile 48k. Ornekleri tepe -6 dBFS'e normalize et, olaylara gore kes (tepe zamanini RMS ile bul), muzigi anlatim zarfiyla duck et (-25 dB konusurken, -17 bosta), sonuc -16 LUFS / tepe -2.4 dBFS (tools/sfx3.py). Sentetik beyaz gurultu 'su dokme' cizirti gibi duyuldu -> gercek kayit kullan. Hesapta odenmemis fatura uyarisi var; abonelik dusarse indirme durur.
