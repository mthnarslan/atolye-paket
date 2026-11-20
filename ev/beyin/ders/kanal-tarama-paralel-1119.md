---
tur: ders
aciklama: Kanal yüzsüz taraması sıralıyken 1,5 dk/kanal; 6 paralel + biten kanalı atla ile 54 kanal ~15 dk; düşük RAM'de MemoryError, yeniden ile düzelir
kaynak: ytmarket_run/reports/kanal1113/kanal100.py
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# kanal-tarama-paralel-1119

kanal1113/kanal100.py tam: sıralı döngü gemweb ~60 sn bekliyordu (30 slot varken 1 kullanıyordu). ThreadPoolExecutor K100_PAR=6 + big4.json'da bitmiş kanalı atla → 89 kanal 19:09–19:30. Boş RAM 0,5 GB iken 3 MemoryError; 'yeniden' komutu düzeltti. Sonuç 24/89 geçti (60 NOT_FACELESS). Ders: gemweb'e görsel istek atan her tarama döngüsü baştan paralel yazılmalı.
