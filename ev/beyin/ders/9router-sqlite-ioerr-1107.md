---
tur: ders
aciklama: 9router 'disk I/O error' koku: surucu sql.js (WASM, bellekte) + buyuyen usageHistory; 11-09 kalici cozum better-sqlite3 + budama + bekci
kaynak: oturum 2026-11-07; gaia_1108 oturumu; VDS 9router 11-09 oturumu
olusturma: 2026-11-07
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# 9router-sqlite-ioerr-1107

Belirti: her modelde 0,1 sn'de 500 Internal Server Error; pm2 status online; 9router-error.log 'disk I/O error' tekrari. Disk %46. Teshis: /opt/9router/data/db altinda data.sqlite-wal/shm yok (silinmis; kim sildi bilinmiyor, 16:40 autobak zamanina yakin). Cozum (kullanici onayiyla): cp -p data.sqlite data.sqlite.bak-ioerr-1107; pm2 restart 9router (reboot yok, --update-env yok). Sonra 3 Flash modeli 4 sn'de 200. Main pipeline gemini_keys yedegine sadece cooldown'da gecer; sf.py/factcheck/ses gecidi yedeksiz.

## 2026-11-08 (claude)

2026-11-08 ~22:09 tekrar: asama 3 grid_prefilter_failed (flash 500, 2 deneme, ~340 sn kayip/cekim), hiz 10 dk'da 150->61 cekime dustu. Yine data.sqlite-wal/-shm yok. cp -p data.sqlite data.sqlite.bak-ioerr-<tarih>; pm2 restart 9router -> 3 dk icinde grid_prefilter basarili. DIKKAT: yedek adina saat ekle (bak-ioerr-1108 adinda 03:29 yedegi vardi, ustune yazildi). Kalici cozum acik: wal/shm'yi kim siliyor (autobak?) bulunmali; bekci 9router-error.log'da 'disk I/O' gorunce otomatik restart edebilir.

## 2026-11-09 (claude)

Kok (11-09): 9router 0.5.112 better-sqlite3 olmadan geliyor -> '[DB] Driver: sql.js'. sql.js tum DB'yi WASM bellekte tutar, her yazmada 100 ms sonra TUM dosyayi export+writeFileSync eder; usageHistory 74k satir/37 MB'a buyuyunce usage yazimlari 'disk I/O error' verip Flash 500 doner (eski WAL/shm teorisi yanlis: sql.js WAL kullanmaz). Kalici cozum: /opt/9router'da 'npm i better-sqlite3@^12' (package.json'a kayitli, guncellemede kalir; Node 20 native) -> log '[DB] Driver: better-sqlite3'; Flash 22 sn -> 2,7 sn. usageHistory 14 gunden eski satirlar silindi (37->23 MB), cron 04:17 /opt/9router/prune_usage.py db 14. dbbak.sh artik 'sqlite3 .backup' (WAL'da cp eksik kopya verir). Bekci cron */2 /opt/9router/wd9.sh: hata logunda yeni 'disk I/O' -> pm2 restart, kayit data/wd.log. Driver tekrar sql.js gorunurse: better-sqlite3 node_modules'tan dusmus, yeniden kur.
