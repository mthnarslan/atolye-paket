---
tur: ders
aciklama: Kapak icin G-Labs: yerel upscale (kota yok) + nano_banana_pro i2i gercek kare + rakip hit referansi
kaynak: testbench/kapak_kare 11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# glabs-kapak-upscale-i2i-1118

G-Labs /api/upscale/generate yerel Real-ESRGAN: hesap kotasi yemez, tek GPU sirayla calisir; 640x360 -> 2560x1440 ~126 sn (kare_sec CPU yukuyle olculdu). YouTube'dan 1080 indirmeye gerek kalmaz (yt-dlp indirme oturumu 2 videoda 1 saat rate-limit'e sokmustu). nano_banana_pro reference_images=[gercek kare, rakip hit kirpimi] + 'image 2 sadece isik/kompozisyon' istemi: ~130 sn, gerceke sadik cilali 1376x768. Model ai_ref'ten bazen uzaklasip yeni sahne kurar; olcek karsitligi istemde acik yazilmali. Hat: testbench/kapak_kare/hat.py (spec_gem.py gemweb high tek istek/video). ffmpeg'de -vsync yok: -fps_mode kullan.
