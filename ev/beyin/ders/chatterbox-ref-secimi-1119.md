---
tur: ders
aciklama: Chatterbox ML: referans sesi degistirmek kisaltma yeniden yazimindan cok etkili (PT 96->74, KO 88->75); Gemini ses hakemi ayni dosyaya 5 ile 96 arasi veriyor
kaynak: testbench/metin_kural_1118/dil_test/kanit3/ses/*_dinle.json
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# chatterbox-ref-secimi-1119

11-19 ses_kol2 (dinle3, 3 kosu ortanca, duz = tum cumleler notr .5/.5): PT_1 duz 96, kisaltma->dogal ifade (_k) 90, _k + tur_suc_pt_1.wav ref 74; KO_1 duz 88, _k 92, _k + insan ref (demucs vokal 10 sn, refs/insan/ko_ref.wav) 75; FR_1 duz 76. Tek kosular 5-8 ile 74-96 arasi oynuyor -> 3 kosu yetmez, karar icin >=6 kosu ya da cok dosya. Kisaltma yeniden yazimi model kodlarini atip olgu kaybettiriyor, kazanc yok -> kullanma. Ref secimi: dil basina birkac ref dene, en dusugu sec.
