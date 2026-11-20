---
tur: ders
aciklama: 9router 35 antigravity hesap: 9 Kas sonu 8 aktif saglam (5 eski + yok, ham + joh 429); 25 TOS/404 kapali
kaynak: VDS /opt/9router/data/db + pm2 log, 2026-11-09; VDS /opt/9router/data/db usageHistory + pm2 log, 2026-11-09; VDS 9router DB 2026-11-09
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# antigravity-ban-codex-1109

9router DB: 35 hesap; 22 TOS 403 (13'u 4-5 Kas, 9'u 9 Kas 12:18-12:19 UTC ayni dakika), 1 NOT_FOUND, 5 saglam ama isActive=0 (jl0,yok,rob,ham,ozt; muhtemelen 11-06 yavas hesap kapatmasi), 5 aktif saglam. Aktiflerin cogu flash-low haftalik kota CACHE_BLOCK (14 Kas'a kadar). Ban oncesi trafik: 03 UTC'den beri codex exec Flash iscileri (/v1/responses, cagri basi ~100-170k token) saatte 37-71M prompt token; uretim (/v1/chat/completions) eskiden saatte 1-30M. Proxy sebep degil (10/10 proxy active; ban hesap duzeyinde). Ders: Antigravity hesaplarini agentic codex isci yuku icin kullanma; codex iscileri GPT'de kalsin, Flash sadece uretim cagrilari.

## 2026-11-09 (claude)

DUZELTME: ilk notta '9 hesap 9 Kas 15:18'de banlandi' yanlis. lastErrorAt yalniz son tekrar denemesi; usageHistory son 'ok' zamani 6-7 Kas -> ban o zamandan. isActive=1 birakilan 9 TOS hesabi 9router surekli deniyor: 30 dk'da 679 adet 403, 2 basari (gurultu + Google'a kotu sinyal). Hesap kontrolu: usageHistory'de connectionId bazinda max(timestamp) where status='ok' ile lastError'i birlikte oku. 14 kapali TOS hesabi denenmiyor; geri geldi mi bilmek icin dashboard Test (giris ister). Codex /v1/responses yuku 9 Kas 03 UTC'den beri saatte 37-71M token: ban sebebi kanitli degil ama kalan hesaplar icin risk.

## 2026-11-09 (claude)

9 Kas 15:52: 'saglam ama kapali' 5 hesap acildi -> jl0, rob, ozt ilk istekte TOS 403 (kapaliyken banlanmis, DB'de lastError yoktu cunku denenmiyordu). isActive=1 TOS hesaplar (12) kapatildi; aktif 8; probe flash-low 6/6. Ders: kapali hesabin 'active' testStatus'u bayat; acmadan saglam sanma. Yedekler autobak/data-before-enable5-*, data-before-disable-tos-*.
