---
tur: ders
aciklama: 13 Kas: 9router'da yalnız 4 antigravity hesabı aktif, 2'si 14 Kas ~08 UTC'ye kadar kota bloğunda; flash-low 'Say OK' 8–50 sn. Ağır paralel test açma, film tek tek; SearXNG için Docker başlat
kaynak: ssh VDS sqlite + pm2 logs, preflight.py 2026-11-12
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# flash-kapasite-1113

Ölçüm 2026-11-12 akşamı: providerConnections antigravity aktif 4/35; 238fb395 ve ed59089c CACHE_BLOCK (low+high) 14 Kas 07:56/08:23 UTC'ye kadar. flash-low 4 istek 8,4/14,7/43,8/49,5 sn; high 3–16 sn, ara sıra 503 MODEL_CAPACITY_EXHAUSTED. preflight Flash'ı 20 sn zaman aşımıyla FAIL gösterebilir; istek gerçekte 200 dönebilir (tekrar dene). SearXNG :8888 Docker kapalıyken FAIL. 14 Kas'ta 429 için kapatılan 5 hesap + bloktaki 2 açılır. Bu sürede: yeni film başlatılabilir ama tek film, testbench büyük A/B ertelendi (ranked-backup, [[ranked-backup-ab-1112]]). Kalıcı token tasarrufları aktif: 9router YouTube mime yaması [[9router-youtube-mime-1112]]; makbuz usage'ı istek başına +2000 hayalet [[9router-2k-hayalet-token-1112]]. DOCUMENTARY_RANKED_BACKUP prod'da YOK (yalnız testbench token_1112 dalı), açma.
