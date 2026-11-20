---
tur: ders
aciklama: 9router Flash: 40+ başlıklı sınıflama isteği 150 sn'de bile dönmüyor; 15'lik parça ~10 sn
kaynak: oturum 2026-11-15
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# flash-uzun-liste-zamanasimi-1115

2026-11-15 cikis.py (vidIQ outlier başlıklarını konuya göre ayıklama): ag/gemini-3.8-flash-low/high 40-50 gerçek başlıkla tek istekte bile 75-150 sn zaman aşımı; 'OK' 4 sn, 50 sahte başlık 16 sn, 15 gerçek başlık 10 sn. Çözüm: 15'lik parça, en fazla 3 eşzamanlı, 60 sn sınır. Ayrıca fikir.py import edilince argparse çalışıyor (uclar/sor'u kopyala). VDS GPT :8765 o an 502.
