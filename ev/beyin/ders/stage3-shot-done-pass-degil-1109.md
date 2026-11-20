---
tur: ders
aciklama: events.jsonl shot_done PASS demek degil (review alani REVIEW_REQUIRED olabilir); ilerlemeyi son shot_done.review==PASS ile say. Gaia 5 filmde %12-25 cekim cozulmedi, drive.py set_aside sonra cikar, 3 3 ile yeniden baslat
kaynak: GaiaTrace 1108 parti
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# stage3-shot-done-pass-degil-1109

GaiaTrace 1108: ilerlemeyi benzersiz shot_done ile saydim, 1640'in ~1600'u 'bitti' gorundu; gercekte 296'si REVIEW_REQUIRED (ilgisiz konu, ekranda yazi/logo, pillarbox/dikey, NO_MATCH, SOURCE_CAP_EXCEEDED). Asama 3 '37 unresolved shots; final render blocked' 500 ile dustu; drive.py set_aside_unresolved sonuclari result.before_auto_* yapip exit eder (otomatik yeniden deneme yok, autoresume yoksa elle). Yeniden baslatma: drive.py <film> 3 3 wildlife; rejected.json kalir. Kontrol araci testbench/gaia_1108/tools/status.py ve reasons.py; otomatik yeniden baslatici relaunch_watch.ps1. YouTube-only (kutuphane kapali) havuzda red orani yuksek.
