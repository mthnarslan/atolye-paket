---
tur: ders
aciklama: Arac uyarisiyla yeniden yazim olculeni duzeltiyor, YZ kokusunu degil: kor hakem 85.6->86.2, insan ~10
kaynak: testbench/metin_kural_1118/dil_test/SONUC.md, kanit2/
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# metin-duzelt-olc-1118

10 model metni (ES/PT/FR/JA/KO x2) metin_denetle uyarilariyla gemweb'e yeniden yazdirildi. Arac: ozet kapanis 9->0, uydurma adayi 21->2, CV esik alti 7/8->4/8, kelime ort. -%29. Kor YZ hakemi (hydrogen): v1 85.6, v2 86.2; insan Kurzgesagt ceviri 5-15 (ort 9.8). Hakemin ana sebebi: paragraflar bilgi tablosunu sirayla geziyor + tabela gecisleri. Yan etki: kapanis soru refleksi 8/10, bos dolgu kisa cumle, yeni klise. Sonuc: cozum planlama asamasinda (yapi soru/olay etrafinda, kaynakta dakikada >=3 somut olgu), duzeltmede 'son olguyla bit, dolgu yok'. Araca eklendi: SIRALAMA (sirali cumle acilisi >=5/100 cumle; insan <=3.6) ve --onceki ep*.json (bolumler arasi 4-gram/acilis/kapanis/cumle basi tekrari -> SABLON; insan 0/33 alarm, LimitClock ep04-07 yakalandi). Kanitlanmadi: ana dil okuru, TTS dinleme.
