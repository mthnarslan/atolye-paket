---
tur: ders
aciklama: Ekran kaydi sesinde agir noisereduce(0.95)+agate konusmayi metalik/kesik yapti; hafif afftdn dogal
kaynak: Avenox oturumu 2026-11-17
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: ortak
---
# agir-denoise-ses-bozar-1117

Avenox ekran kaydi sesi: noisereduce prop_decrease 0.95 non-stationary + agate zinciri konusmayi metalik, bogulmus, kesik yapti (kullanici: 'konusma gitmis, bir sey duyulmuyor'; Gemini dogal 6/10). Yerine highpass=80,afftdn=nr=10:nf=-45,adeclick,loudnorm=I=-15: dogal 9/10, anlasilir 8-9/10 (3x ortanca, kontrol/dogallik.py). Kural: temizlikten sonra hakeme sadece 'duyuluyor mu' degil 'dogal mi/metalik mi' de sor. Kod: Kanallar/Avenox_inceleme/araclar/ses_temizle.py
