---
tur: ders
aciklama: gemweb hydrogen ses hakemi: istemde 'efekt eklendi' deme, efektsiz dosyada 8/10 efekt uydurur; yonlendirmesiz istem + 3x ortanca
kaynak: Avenox_inceleme kontrol/hakem_*.txt
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: ortak
---
# gemini-ses-hakem-istem-1117

Avenox 15 sn miks (11-17). Istem 'ustune efekt eklendi' deyince ayni efektsiz dosyaya bir kez 8/1, bir kez 6/8 (konusma/efekt rahatsizligi) verdi, olmayan saniyelerde (3,6,9) darbe/whoosh uydurdu. Yonlendirmesiz istem ('konusma disi duydugun her sesi zamaniyla yaz, duymadigini yazma') + 3 kez sor, ortanca: tutarli 9/1, 9/1, 9/2. Arac: Kanallar/Avenox_inceleme/araclar/ses_hakem.py. Ham ekran kaydi gurultusu (tik, kus, ugultu) loudnorm ile +28 dB buyuyordu: noisereduce stationary=False prop 0.95 + adeclick + agate + loudnorm (araclar/ses_temizle.py, venv .venv_df; deepfilternet libdf derlenmedi). Efektler 0.07-0.08 seviyesinde, ilk darbe cikarildi.
