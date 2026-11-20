---
tur: ders
aciklama: vidIQ kredi tasarrufu: channel_videos YouTube API'ye, akilli onbellek suresi, surec butcesi, defter, bakiye kapisi
kaynak: oturum ca24718b 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# vidiq-kredi-tasarrufu-1110

ytmarket_run/bin/vidiq.py (yedek .bak1110): 1) vidiq_channel_videos otomatik bin/ytapi.py'ye gider (YouTube Data API, KEY.txt anahtarlari, 0 kredi, 24 sa onbellek); 6 kanalda ayni video/sure, izlenme daha guncel. Kapat: VIDIQ_CV_VIA_YT=0. Kaçagin %57'si buydu. 2) day=True artik 'bugun' degil arac basina sure: outliers/similar 7 gun, get_channels 3, earnings 90, keyword 30. 3) Ayni anda ayni soru tek odenir (anahtar kilidi). 4) Surec basi tavan VIDIQ_BUDGET (varsayilan 1200 kredi) -> BudgetExceeded. 5) Her gercek cagri secrets/vidiq_ledger.tsv'ye (zaman, arac, kredi, betik) - kim harcadi sorusu artik kesin. 6) market_report.py basinda bakiye kapisi (<500 ise durur, VIDIQ_FORCE=1). Soguk tam pazar raporu ~1000 -> ~500 kredi, 7 gun icinde tekrar ~0. Dogrudan MCP'de de kanal videolari icin vidIQ yerine ytapi.channel_videos kullan.
