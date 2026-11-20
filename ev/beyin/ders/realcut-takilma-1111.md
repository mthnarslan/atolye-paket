---
tur: ders
aciklama: LIMIT CLOCK realcut: tek takilan indirme/proxy tum bolum taramasini kilitler; toplam sure siniri sart
kaynak: ZeroPulse/LimitClock logs/realcut2_ep04.log
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# realcut-takilma-1111

11-11 ep04: tarama 00:18'den sonra 23 dk hic log yazmadan takildi (SOCKS proxy 'Connection refused' sonrasi bir is parcacigi asili kaldi; ThreadPoolExecutor.map hepsini bekledi). Ayrica spor konusu (futbol/kalp) YouTube'da neredeyse hep yayin logosu, altyazi, roportaj kesmesi tasidigi icin 53 aday reddedildi; konu secerken bunu hesaba kat. Cozum: realcut.py artik -tmax (varsayilan 2400 sn) ile futures+wait kullanir, gec kalan kesit murekkep gorsele duser, sonda os._exit ile asili thread beklenmez. Takilan taramayi elle bitirme: sureci oldur, plan.json'da mp4'u olmayan r_ kesitleri still'e cevir, loga 'REAL DONE' yaz.
