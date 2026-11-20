---
tur: konu
aciklama: Ortak Atölye /trend/: ABD Google Trends + YouTube 48 sa izlenme/outlier, kanal eşleşen satır renkli; saatlik OrtakTrend görevi
kaynak: oturum 2026-11-13
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# abd-trend-sayfasi

Betik ortak-site/tools/trend_push.py (Trends RSS geo=US, istek başına yalnız 10 konu, saatlik birikir, 48 sa pencere; YouTube araması konu başına 12 saatte bir 100 birim; kanal eşleşmesi Flash low konu başına bir kez, ipuçları HINTS sözlüğünde). Veri /ingest/trend (WRITE_TOKEN) -> D1 kv 'trend' -> /api/trend. Windows görevi OrtakTrend (pythonw, saatte bir, log tools/trend_push.log). PC kapalıyken güncellenmez. Yeni kanal: kanallar.json + HINTS + sayfadaki COLORS.
