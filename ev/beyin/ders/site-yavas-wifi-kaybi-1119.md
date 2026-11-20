---
tur: ders
aciklama: Site/sekme yavaşlığı ölçümü: sunucu 0,1 sn, takılma Wi-Fi paket kaybında (modeme %20, 1.1.1.1'e %67 kayıp)
kaynak: oturum 5d5f6be9, ortak-atolye.vercel.app ölçümü
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# site-yavas-wifi-kaybi-1119

11-19 Ortak Atölye Kapaklar yavaş şikayeti. Ölçüm: sekme render 33-83 ms, istekler normalde 150-250 ms; rastgele isteklerde 10-28 sn takılma. curl time_connect/time_appconnect takılmayı TCP/TLS kurulumunda gösterdi (sunucu ttfb ~0,1 sn). Kontrol grubu (google, cloudflare, github) da 6-11 sn takıldı; Test-Connection modeme 24/30 (maks 1946 ms), 1.1.1.1'e 10/30. Sonuç: kod değil yerel Wi-Fi. Yöntem: önce curl -w connect/appconnect + kontrol siteleri + ping kaybı; sonra kod profili.
