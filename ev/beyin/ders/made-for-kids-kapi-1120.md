---
tur: ders
aciklama: Kanal önerisinde madeForKids sert kapı: kanal ya da örnek videoların >=%50'si true ise ele (düşük RPM, yorum kapalı); ytapi.made_for_kids
kaynak: kanal1120/tazelik_yeni6_1120.json
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: ortak
---
# made-for-kids-kapi-1120

11-20: Little Oops English tazelik/yüzsüz/örnek kapılarını geçti ama kanal ve 8/8 video madeForKids=True çıktı, elendi. Araç: ytmarket_run/bin/ytapi.py made_for_kids(cid, videoIds) (2 birim), yeni_1120.py tazelikten sonra sert kapı. Sitedeki 88 kanal tarandı: 0 kids (kanal1120/kids_site_1120.json).
