---
tur: ders
aciklama: Ortak Atolye hesaplar sayfasi ara sira bozuluyordu: .pw sinifi kanallar-yeni/pencere.css'teki pencere .pw ile cakisti
kaynak: oturum 2026-11-18, commit ortak-site
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# ortak-site-css-cakisma-1118

Sifre butonu class 'pw' idi; kanallar sayfasi pencere.css'i yukleyince .pw{width:min(1040px,100vw-24px)} butona uyguladi, sifre sutunu 1040px olup tabloyu tasirdi (yalniz o css yuklenince -> 'ara sira'). Cozum: .pwd + .app/#hesaplar grid-template-columns:minmax(0,1fr). Ders: index.html'e baska sayfanin css'i yukleniyor; kisa genel sinif adi (pw, px, cp) kullanmadan once grep -rn ile public/ altinda cakisma ara.
