---
tur: ders
aciklama: Dublaj kotu cikiyordu: arka plan muzigi yoktu, 15 sn ada + hizli erkek ses + kelime kelime ceviri. Duzeltme: demucs bed + cumle basinda baslat + ~5.5 hece/sn serbest gunluk ceviri + tasarlanmis kadin ses
kaynak: testbench/dub_1112/v2, ref/
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# dublaj-pro-fark-1113

11-13 kullanici 'araliklar bos, izleme keyfi yok' dedi. Referans: Isaac QXfugR3ZIAs (YouTube coklu ses, tr izi) olculdu: TR cumleleri EN cumle baslarinda basliyor, toplam konusma suresi ayni (94.8 vs 93.7 sn), ~5.7 hece/sn konusma, 351 EN kelime -> 258 TR kelime, cok serbest gunluk uyarlama ('vallahi', 'oglum', 'abi'), arka plan muzigi hep var. Bizim hatalar: mix.py arka plani tamamen atiyordu (sessiz bosluklar), 6-15 sn ada icinde dogal duraklar kayboluyordu, refC 8.5 hece/sn kosuyordu, kadin konusmaciya erkek ses, ceviri hece sayisina gore uzatilmis. Yeni yol testbench/dub_1112/v2: bed.py (demucs htdemucs 2-stem, asker venv), cumle bazli segs.json (start=EN cumle basi), gen.py (OmniVoice; once instruct='female, young adult, moderate pitch' ile bir cumle tasarla, sonra o wav'i klon referansi yap -> tutarli ses), mix2.py (cumle orijinal basinda, hiz degisimi yok, ses rms/bed orani orijinaldeki gibi ~12 dB). Gercek konusmacinin Ingilizce sesini klonlamak aksan tasidi (Whisper 2/3 cumleyi EN sandi) -> kullanma. Sessiz bosluk 9 -> 1, 13/13 cumle back-check dogru. Bas harfi C ile baslayan 'Calistigim' tekrar tekrar 'Konustugum' okundu -> cumleyi degistir.
