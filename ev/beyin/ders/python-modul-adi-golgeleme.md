---
tur: ders
aciklama: Script'e stdlib adını (_queue.py, queue.py) verme: alt süreçler onu import edip kendini tekrar başlattı, 349 süreç, RAM 0
kaynak: Engineered scenefile 6 Kas
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# python-modul-adi-golgeleme

scenefile/_queue.py: subprocess ile sf.py çalışınca 'import queue' -> C _queue yerine bizim _queue.py yüklendi, o da kuyruğu yeniden başlattı (çatal bombası). Bekçi ajan yakaladı, filmqueue.py olarak adlandırdı. Kural: yardımcı script adları stdlib ile çakışmasın (queue, _queue, select, types, json, random...).
