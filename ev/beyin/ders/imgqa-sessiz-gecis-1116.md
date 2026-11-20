---
tur: ders
aciklama: LimitClock imgqa: Flash 503 doneninde tum gorseller 'error' alip '0 bad' basiyordu (sessiz gecis); artik gemweb once, hata sayisi UNCHECKED diye basiliyor
kaynak: ZeroPulse LimitClock ep06-10
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: ortak
---
# imgqa-sessiz-gecis-1116

16 Kas ep06-10: 86 gorselin hepsi HTTP 503 ile kontrol edilmedi ama cikti '0 bad' dedi. Duzeltme lc/imgqa.py: gemweb.sor_json(Q,[png]) once, Flash yedek; error sayisi UNCHECKED olarak yaziliyor. Gercek kontrol 1 yazili gorsel buldu (istem 'CO2 bubbles' dedigi icin; istemde etiketlenebilir nesne adi verme: 'plain blank unmarked bubbles'). Hakem ciktisinda hata = gecis sayilmamali.
