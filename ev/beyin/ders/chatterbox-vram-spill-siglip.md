---
tur: ders
aciklama: Chatterbox yavasligi = VRAM tasmasi; :8099/reload + Chatterbox restart 4.9->34.8 tok/s
kaynak: ENGINEERED parti oturumu 2026-11-05; ENGINEERED fullrun 1106
olusturma: 2026-11-05
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# chatterbox-vram-spill-siglip

2026-11-05: Jeff sesi (Chatterbox :7864) saniyede ~1,2 token'a düştü (normali 5-6+). Sebep: ses servisi kapalıyken picture_fit SigLIP modeli karta yüklenmiş (köprü 839 MB). Servis geri gelince 2714 MB kartta + 726 MB paylaşımlı bellekte kaldı. Teşhis: PowerShell Get-Counter '\GPU Process Memory(*)\Shared Usage' ile pid başına paylaşımlı bellek. Çözüm: model_memory.py release_picture_fit_gpu() ses portu açıkken SigLIP'i işlemciye alıyor; modül yüklenince çalışıyor, GET :8099/reload ile tetiklenir. model_memory.py hiçbir çekim kimliğinde yok, biten çekimler yeniden yapılmaz. Sonra Chatterbox'ı yeniden başlat: 3211 MB kartta + 120 MB paylaşımlı, 5-6 token/sn. sopro_voice_client bağlantı hatasında 1 kez yeniden deniyor, ilerleme kaybolmuyor.

## 2026-11-06 (claude)

2026-11-06 fullrun: 4 film paralel ses asamasinda Chatterbox 3-5 tok/s (dakikada 1 parca). Kopru (pid 28180) 673 MB kartta tutuyordu, Chatterbox 266->516 MB paylasimli. GET :8099/reload kopruyu 237 MB'a indirdi ama Chatterbox kendiliginden geri donmedi; Chatterbox'i oldurup Start-Chatterbox.ps1 ile baslatinca 14 sn'de ayaga kalkti, 3195 MB kart + 78 MB paylasimli, 34.8 tok/s (7 kat). Kontrol: Get-Counter '\GPU Process Memory(*)\Shared Usage' Chatterbox pid'inde >150 MB ise ayni islem.
