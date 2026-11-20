---
tur: ders
aciklama: HyperFrames kurucuda sira-numarali asset adi (iNNN) + 'varsa kopyalama' = ret/yeniden kurulumda etiket-foto kaymasi; kaynak haritasi + bayat parca silme
kaynak: Kanallar/Grenzakten_uretim/gz_build.py
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# hf-asset-ad-kaymasi-1118

Grenzakten 11-18: gz_build assetleri kurulus sirasina gore i000.jpg.. adlandiriyor, dosya varsa kopyalamiyordu. ret.txt degisince ayni ad baska fotoya gecti, eski dosya kaldi: render'da 'Angela Merkel' etiketinde 1953 tanki, 'Conradi' etiketinde Reagan, 'Bonn 1994'te Reichstag yangini. Html dogru gorunur, hata yalniz videoda. Cozum: assets/map.json (ad->kaynak), kaynak degisirse yeniden yaz + parcayi bayat say; html degisirse ya da out.mp4 html'den eskiyse out.mp4 silinir (render atlama yalniz sureye bakiyordu). Kontak QA'da etiket-goruntu celiskisi gorursen once asset dosyasini kaynakla karsilastir.
