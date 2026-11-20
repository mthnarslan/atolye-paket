---
tur: ders
aciklama: trend_push kota: web araması kotasız, API yalnız eşleşen/>=20K konuda (tavan 5k/gün), genç konu her saat; ölçüm ~25 birim/koşu
kaynak: oturum 2026-11-14; ortak-site tools/trend_push.py
olusturma: 2026-11-14
guncel: 2026-11-14
yazan: claude
onay: 
etiket: 
---
# trend-kota-1114

Google Trends RSS her saat ~10 yeni konu veriyor (48 sa'te ~480). search 100 birim; 12 saatte bir yeniden arama günde ~96k birim eder, 5 YouTube anahtarının ~50k kotasını ve diğer ytapi işlerini bitirir. 11-14'te tek aramaya indirildi (~24k/gün); sayılar videos ile saatlik tazeleniyor. Sayfa 15'li sayfalama + 6/24/48 sa filtresi.

## 2026-11-14 (claude)

11-14 son hal: ytapi.py ortak defter (ytmarket_run/cache/../ytapi_usage.json, Pasifik günü, who etiketi; usage('trend')). trend_push: Flash eşleşme önce; her yeni konu yt-dlp web araması (sp CAMSAggC+CAMSAggD, yt_gate 'trend_search'); API search yalnız kanal eşleşmesi ya da traffic>=20K, günlük trend tavanı 5000. Stats: <24 sa konular her koşu, eskiler 6 sa; konu başına 15 video; abone önbelleği state['subs'] 48 sa. Ölçüm: ilk koşu 63 birim (tam tazeleme), sonraki 25 birim/koşu → ~600/gün + API aramaları (eskisi ~24k+4.6k/gün). Web araması API ile örtüşmesi düşük (7 konuda 0-10/10) ama kota yemez. ytapi.py yedeği ytapi.py.bak-1114.
