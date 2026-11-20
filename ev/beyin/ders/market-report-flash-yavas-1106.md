---
tur: ders
aciklama: market_report.py: Flash-low 25 başlıklık liste sınıflaması 159 sn; regex filtresi kirli; nişte eleme elle (Claude) yapılır
kaynak: ytmarket_run/reports/r1106
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# market-report-flash-yavas-1106

11-06: 9router Flash-low kısa istem 4,8 sn ama 25 başlık sınıflama 159 sn → market_report.py onniche/lookalikes Flash'sız (NEG regex + başlık kök örtüşmesi >=2). Regex tek başına kirli (fr örnekleri Peppa Pig, balık): ≥100k başlıkları hits_all.txt'e döküp ana oturum elle eler. vidIQ 429: vidiq.py 6 deneme geri çekilme; steadiness hatası atlanır. Benzer kanal: kanal modu similar kötü (alakasız belgeseller), niş modu + kök örtüşmesi daha iyi; ilk sürüm 'true/story/alone' gibi genel kelimeyle aşk/vlog kanalı seçti, STOP listesi eklendi.
