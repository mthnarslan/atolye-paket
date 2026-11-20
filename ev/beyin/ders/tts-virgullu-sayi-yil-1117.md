---
tur: ders
aciklama: TTS metin cevirici: '1,000' virgulu silinip yil kuralina girdi -> 'ten hundred', '1,845' -> 'eighteen forty-five'; virgullu sayiyi once cardinal cevir
kaynak: km6 2026-11-17
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: ortak
---
# tts-virgullu-sayi-yil-1117

KINGMAKERS km6 lines.py tts(): virgul silme adimi yil kuralindan (1000-2099 -> 'sixteen ninety-eight') once calisiyordu; '1,000 men' 'ten hundred men', '1,845 sent' 'eighteen forty-five sent' diye seslendirildi. Whisper orneklemesi (60 satir, ort. 0.94) bunu tek satirda yakaladi; virgullu tum sayilari tarayinca 3 satir cikti. Cozum: \b\d{1,3}(?:,\d{3})+\b once num2words ile sayi olarak cevrilir; yil kurali yalnizca virgulsuz 4 haneye. Ayrica: lines.py modul seviyesinde calisir, 'import lines' tum lines.json'lari kaynaktan yeniden yazar ve sonradan uygulanan script_fix (benzerlik denetimi) duzeltmelerini siler -> import etme, ya da script_fix'i yeniden kos. Seslendirilmis filmde tek satir degisince yeni kaydi eski sureye pad/atempo<=8% ile oturt, timeline yeniden kurulmaz.
