---
tur: konu
aciklama: 18 Kas: 20 yeni nis kanal eklendi (59 ornek)
kaynak: oturum 2026-11-13; ortak-site tools/kanallar_yeni_build.py; oturum 2026-11-15; ortak-site 8c28d19; ortak-site commit 16 Kas; ytmarket_run/reports/hafta1118, ortak-site commit
olusturma: 2026-11-13
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# yeni-kanallar-sayfasi

Veri ytmarket_run/reports/kanal1113 (ornek.json, big.json, big2.json; ölçüm big.py forHandle 1 birim). Sayfa verisi ortak-site/tools/kanallar_yeni_build.py -> public/kanallar-yeni/data.json; yenilemek için big.py'yi koş, build'i koş, wrangler deploy. Ustalar filtresi: 1M+ abone, 90 günde ≥1 uzun video, medyan ≥100k, örnek listesinde olmayan; 6 grup (G dict). Pasif çıkanlar: OverSimplified, LEMMiNO, CGP Grey, Defunctland, Nexpo, PolyMatter, MagnatesMedia, Barely Sociable.

## 2026-11-14 (claude)

11-14: ustalar bölümü sadece faceless (sunucu kamerada değil). Yüzlü/TV kanalları kanallar_yeni_build.py FACE listesinde; yeni faceless adaylar big3.py -> big3.json (kanal başına ~3 birim). Faceless yargısı kanal bilgisinden, kare kontrolü yapılmadı.

## 2026-11-15 (claude)

2026-11-15: Her örnek kartta 'Dil · benzerler · 2 usta' düğmesi -> dialog. Veri ytmarket_run/reports/kanal1113: benzer.py (vidIQ similar_channels channelId, 29x5 kredi; yalnız aynı dil döner), dil.py (21 niş x 5 dil niche+language, 105x5 kredi) -> dil.json; USTA2 eşlemesi tools/kanallar_yeni_build.py. Dil önerisi = küçük başarı (abone<50B, ort>=20B) x RPM (en 3.42, de 2.22, ja 1.88, es/pt 1.37). vidIQ bakiye 3201 -> 2676. Kriegsingenieure için vidIQ İspanyolca benzer döndürdü (boş gösterilir). Commit ortak-site b8a44c9.

## 2026-11-15 (claude)

2026-11-15: Ana sayfada kendi kanalına tıklayınca vitrin penceresi açılıyor (public/kanallar-yeni/pencere.js PW.vitrin, veri vitrin.json). Veri: ytmarket_run/reports/kanal1113/cikis.py — vidIQ outliers, tohum video + 5 dilde anahtar sorgu (52 çağrı, ~260 kredi, önbellekli; bakiye 2411), x>=3 uzun video, kanal başına ilk 90 aday; konu ayıklaması keep.json (Haiku alt ajanı; Flash 15'lik parçada bile yavaştı). 264 patlayan video. Yenilemek için: cikis.py --aday -> keep.json -> cikis.py -> tools/kanallar_yeni_build.py -> wrangler deploy. Örnek kart penceresi PW.ornek; kanal adları lang=en (Türkçe büyük harf İ hatası).

## 2026-11-16 (claude)

16 Kas: 10 yeni kanal (son 1 hafta patlayan) eklendi. Yontem ytmarket_run/reports/hafta1116: vidiq_outliers publishedWithin=thisWeek, 8 dil (en es de pt fr ja ko it), dil basi genis + 10 konu anahtar kelimesi; ~520 kredi. Eleme: yas<=200 gun, top>=120k, <=200 video; skor.py YouTube API ile med10/hafta_top; son.py yt_ad + kare sayfasi ile faceless kontrolu. Ekleme kanal1113/ekle1116.py -> ornek.json sonuna (sitede son sira), dil.py NIS+CH, benzer.py, USTA2 build'de. Deploy wrangler pages.

## 2026-11-18 (claude)

hafta1118 yontemi: 20 yeni nis anahtari x 7 dil (en es de pt fr ja ko) + 12 dilde genis vidIQ outliers thisWeek; ~1315 kredi (7177->5862). Havuz 5474 -> liste 257 (yas<=200 gun, top>=100k, <=150 video, Guney Asya/SEA haric) -> skor + reklam + kare sheet ile yuzsuz secim; 16 reklamli, 4 reklamsiz. Siteye: kanal1113/ekle1118.py, dil.py (yeni NIS anahtari), benzer.py, logo doldur; USTA2 handle'lari big'de olmali (LessonsfromtheScreenplay/DarkDocs yok). ads2.json'u ads.json'a birlestirmeden ekle betigi KeyError verir.
