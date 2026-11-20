---
tur: ders
aciklama: Lumit ile .aep açma işe yaramaz: içe aktarma yalnız arayüzden, yazı animasyonu/font/renk taşınmıyor, 30 sn comp 295 sn; paket önizlemesi için paketin kendi gif'lerini kullan
kaynak: testbench/atomx_1111, ortak-site/tools/build_stil.py
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# lumit-aep-yolu-olmaz-1111

AtomX demo paketleri (Spunkram AE, Zeoside Premiere) Adobe'siz gösterilecekti. Lumit v0.11.1 denendi: .aep içe aktarma yalnız GUI (File > Import .aep), lumit-cli sadece export; çıktı yanlış (text animator, font, renk yok), 30 sn comp 295 sn. GUI otomasyonu bilgisayarı çok yavaşlatıyor (kullanıcı şikayeti): GUI kullanma. Çözüm: paketlerin 'Atom Preview Assets' gif'leri gerçek görünüm; ortak-site/tools/build_stil.py gif->mp4 (480x270) + wav->mp3 + data.json üretir, sayfa public/stil/. 153 şablon, 37 ses, 13 MB; medya (public/stil/a) git'e girmez, deploy ile gider.
