---
tur: ders
aciklama: Kanal-çifti gömme kapısında U eşiği aynı-kanal split-half P10 olursa farklı kanal neredeyse hiç U alamaz (5/5 aday Z)
kaynak: ytmarket_run/reports/kanal1120/gomme_kapi/gomme_sonuc.json
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# gomme-kapisi-split-half-sert-1120

11-20 Bulucu: e5-base centroid kosinüs, 5157 çıpa kanal, aynı dil negatif; AUC 0,998 (MiniLM 0,981). Eşikler ja P10 0,979/negP90 0,952. 5 adayın 10 örnek çiftinin 9'u Z, 1'i Y, U yok. Ders: pozitif çıpa aynı kanal yarıları olunca U = 'aynı kanal kadar benzer' olur; farklı kanal-aynı niş için ayrı pozitif çıpa (ör. vidIQ similar / bilinen aynı-niş çiftleri) ÖNCEDEN kaydedilmeli. Ayrıca e5 skorları 0,87-0,98 dar bantta. LLM yargıç (Haiku 3/6, Sonnet 1/6) yerine deterministik ve geçerli. CPU'da e5 5157 kanal ~45+ dk, GPU'da dakikalar: GPU boşsa GPU kullan. Venv: testbench/gomme_venv.
