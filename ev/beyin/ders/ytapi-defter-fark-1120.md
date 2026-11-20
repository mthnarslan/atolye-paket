---
tur: ders
aciklama: ytapi defteri Google kotasından ~3.400 birim düşük çıktı: 12 dosya KEY.txt ile YouTube Data API.yi doğrudan çağırıyordu (2 dosya editscan scan/probe_yturl Gemini anahtarı, dokunulmadı); artık tek yol ytapi.py
kaynak: ytmarket_run/secrets/ytapi_usage.json; Bulucu oturumu 11-20
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: ortak
---
# ytapi-defter-fark-1120

11-20: Google tek anahtarı 10.000 birimde bitmiş saydı, ytapi_usage.json 6.624 gösterdi (k1120d'nin 2.827 doğrudan birimi sonradan eklendikten sonra). Grep (Kanallar, SkullStudio, ytmarket_run; KEY.txt|googleapis.com/youtube|youtube/v3) ytapi.py dışında 14 dosya buldu (bin/monet_probe, chan_score, chan_videos, format_test, check_pass, niche_hunt, probe_keys; rakip1113/vids, chk; editscan/flow, resolve, scan, discover, probe_yturl). Kayıp ~3.400 birimin kaynağı kanıtlanamadı (bugün hangisinin koştuğunu gösteren log yok). Çözüm: 13 dosya ytapi.api(who=dosya) üzerinden geçirildi (.bak-1120ytapi), probe_keys.py yalnız sınama aracı olarak işaretlendi. Kural: YouTube Data API'ye yalnız ytapi.py ile git; yeni betikte KEY.txt okuma yok; kontrol için yukarıdaki grep.
