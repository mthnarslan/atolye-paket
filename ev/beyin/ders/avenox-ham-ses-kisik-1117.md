---
tur: ders
aciklama: Kullanicinin ekran kaydi sesi cok kisik (~-43 dB); normalize etmeden SFX eklenince konusma duyulmuyor
kaynak: Avenox oturumu 2026-11-17, kullanici sikayeti
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: 
---
# avenox-ham-ses-kisik-1117

Avenox ham kayitlari ortalama -43 dB. Miks: ses highpass80+afftdn+loudnorm I=-16, SFX x0.35 ve sidechaincompress ile konusma altinda kisilir (araclar/karma.py mux). Kontrol: final miksi faster_whisper ile yaziya dok, cumleler okunuyorsa tamam. SFX'i hic bir zaman ham seviyeye gore ayarlama.
