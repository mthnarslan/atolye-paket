---
tur: ders
aciklama: 15 Kas 14:42'den itibaren 15 antigravity hesabının 10'u TOS 403 ile banlandı; 5 aktif kaldı (4 çalışır, 1 kota 429). Flash kapasitesi yine dar
kaynak: 9router pm2 logs, /tmp/agp3.py 15 Kas 14:50
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# flash-ban-dalgasi-1115

Sabah 11:2x probu 15/15 hesap 200 dönüyordu. 14:42'den itibaren 9router logunda 'This service has been disabled in this account for violation of Terms of Service' (PERMISSION_DENIED 403); 14:48'de 'all 15 accounts locked'. /tmp/agp3.py probu: 10 hesap 403 → isActive=0 (yedek data.sqlite.bak_1115_ban). Kalan aktif: sou, jer, joh, ejd(adca) 200; the 429 kota. Proxy havuzları 1f16/1351/2389/3e10'daki hesapların hepsi banlandı. Gün içinde yük: ranked-backup büyük A/B (4 film koşusu) + diğer oturumlar. Ağır Flash işini 4 hesaba yüklemeden önce kendi anahtarlarına (gemini_keys.py) geçmeyi düşün.


**15 Kas akşam:** kullanıcı isteğiyle 30 pasif (403 TOS/kapalı) antigravity hesabı 9router'dan silindi (yedek data.sqlite.bak_1115_sil). Kalan 5 aktif hesap havuzları adca, 50b2, 6416, 7c9c, 27c6; boş havuzlar 9c6e, 3e10, 1f16, 1351, 2389 (son dördü banlanan hesaplarla eşleşmişti, yeni hesaba verilecekse en son kullan). Kullanıcının kendi Google hesapları da banlandı, Antigravity IDE'si bu yüzden hata verir.
