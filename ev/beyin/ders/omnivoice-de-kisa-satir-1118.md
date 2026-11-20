---
tur: ders
aciklama: OmniVoice Almanca: kisa satira basa fazladan hece ekler; kisa satiri komsusuyla birlestir, ASR >=0.96 ile sec
kaynak: Ornek_WA 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# omnivoice-de-kisa-satir-1118

OmniVoice OV_LANG=de klonda 1-4 kelimelik satirlar basa uydurma hece aliyor. Kisa satirlari komsu cumleyle birlestir; her satiri 2 seed uret, faster_whisper medium CPU (C:/ yollar) ile ASR oranina gore sec (Ornek_WA/kontrol.py). HyperFrames lint sistem fontu icin de @font-face ister (Bahnschrift'i assets'e kopyala).
