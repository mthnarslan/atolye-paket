---
tur: ders
aciklama: Kapaklar sayfası: kanal çip seçici + kanal paneli + tam genişlik detay; deploy ENOENT'te yeniden dene
kaynak: ortak-site index.html 18 Kas
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# kapaklar-sayfa-duzen-1118

Sol 310px liste tüm kanalları alt alta diziyordu, 20 kanalda dağılır. Yeni düzen: üstte sarmalanan kanal çipleri (logo+ad+video sayısı; 20 kanal masaüstünde 3 satır, mobilde yatay kaydırma), seçili kanal paneli (ZIP, video kartları, 4 hücre kanal analizi), altta tam genişlik detay (sürüm kartları küçük resimli, referans kutusu: ref küçük resim+çarpan | aldık/ekledik/korunan). Doğrulama: localhost:8731 statik sunucu (giriş yok), 375 ve 1440'ta taşma JS kontrolü 0. Başka oturum public/nasil'e yazarken wrangler deploy ENOENT verebilir: tekrar dene. Commit'te yalnız kendi dosyaların (public/v ve dublaj.json başka oturumun).
