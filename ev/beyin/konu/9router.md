---
tur: konu
aciklama: 9router Flash gecidi (VDS :20128): 15 hesap / 10 proxy siraya dizildi 11-14
kaynak: Kanallar/SISTEM.md (4 Kas, 1 Kas); DURUM.md §4; oturum 238b861c 2026-11-05; oturum 2026-11-14
olusturma: 2026-11-04
guncel: 2026-11-14
yazan: claude
onay: 
etiket: llm,altyapi
---
# 9router

VDS 100.104.78.117:20128 uzerindeki Flash ag gecidi; kurulum `/opt/9router` (yerel), model `ag/gemini-3.8-flash-*`. Anahtar `C:\Users\meteh\.gemini\scripts\documentary_voice_gateway.json` icinde (yazdirma).

- **API sadece Tailscale IP'sine bagli:** sunucuda `localhost` ile curl bos doner.
- **Stream:** OpenAI uyumlu cagrida `"stream": false` ver, yoksa SSE doner ve `json.load` "Expecting value" verir.
- **249 sn 502 'fetch connect timeout' (kok sebep, proxy DEGIL):** stream olmayan istekler `generateContent` kullanir, Google basliklari uretim bitince yollar; `FETCH_CONNECT_TIMEOUT_MS` varsayilani 60 sn -> uzun uretim kesilir, 3 yeniden denemeyle 4x60+9 = 249 sn. Cozum: `/opt/9router/ecosystem.config.cjs` env `FETCH_CONNECT_TIMEOUT_MS: '240000'` **ve her env degisikliginden sonra `pm2 save`** (11-06 reboot'ta kayboldu; bkz [[9router-reboot-pm2-dump]]) + chunks 436/2132/9609.js ProxyAgent `headersTimeout/bodyTimeout` 60000->240000 (9router guncellenince bu yama gider, env kalir). Sonuc: 180 sn'lik istek gecti, 10 paralel 10/10 p50 4,6 sn.
- **Paralellik/proxy:** `settings.providerStrategies.antigravity.stickyRoundRobinLimit` 1 olmali (3 iken 10 paralel istek 4 IP'ye gidiyordu); `strictProxy=true` (proxy duserse dogrudan IP'ye dusmez); hesap->proxy `providerConnections.data.providerSpecificData.proxyPoolId`.
- **Yavas hesabi kapatma:** DB yedegi al -> `pm2 stop` -> `providerConnections.isActive=0` -> `pm2 start` (sql.js bellekte tutar; calisirken dis yazma ezilir). Geri acmak ayni yol isActive=1.
- **Restart sonrasi** AG_QUOTA onbellegi sifirlanir: haftalik kotasi biten hesaplar birkac dk 429 (15-20 sn) verip CACHE_BLOCK'a girer; normal.
- **Cokme:** pm2 bellek siniri 2600M, kill_timeout 20 sn (kok sebep SIGKILL); DB 20 dk'da bir yedeklenir (`/opt/9router/dbbak.sh`, cron).
- **Ban:** 1 Kas'ta 23/30 hesap 403 TOS_VIOLATION [[antigravity-tos-ban]]; hesap tokeniyla `loadCodeAssist` govdesine bak (9router log'u yalniz "HTTP 403" yazar); yogun video cagrisi yaptirma.
- **Istemci hatasi:** `image/*` MIME -> 400 "Unsupported mime type"; gercek tur (image/png, image/jpeg) yaz.
- Test: `testbench/router_check/probe.py` (single | par N model); son sonuc 10 paralel 10/10. Yedek: `gemini_keys.py`; havuza ayni istemi toplu gonderme [[gemini-key-pool-block]]. GPT bitince: [[gpt-replacement-model]].

## 2026-11-14 (claude)

11-14: 11 hesap acildi (aktif 15; yedek /root/data.sqlite.bak-1114-enable). Round-robin (stickyRoundRobinLimit 1) LRU sirasiyla doner: 16. istek 1. hesaba gider (dogrulandi). Proxy dagilimi duzeltildi (yedek bak-1114-proxy): eskiden 3 hesap <IP-gizli>'de, 2 proxy bos; simdi her proxy en fazla 2 hesap ve cift hesaplar dongude 10 sira arayla -> 1. ve 11. istek ayni proxy. Hesap->proxy degisince providerSpecificData.proxyPoolId VE connectionProxyUrl birlikte degismeli (9router connectionProxyUrl'i kullanir). Test isteği Tailscale IP'ye (127.0.0.1 dinlemiyor). Log: pm2 logs '[PROXY] ANTIGRAVITY conn=... url=...'. Kucuk istek 3-8 sn (THINK:high), dogrudan 2-4 sn.
