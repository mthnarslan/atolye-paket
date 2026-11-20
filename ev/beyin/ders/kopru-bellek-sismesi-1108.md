---
tur: ders
aciklama: 5 film asama 3 tek koprude 3,5 saatte 12 GB private'a sisti; RAM kapisi bir filmi (EP03) 20+ dk aclikta birakti; kopru yeniden baslatma cozdu
kaynak: gaia_1108 oturumu
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# kopru-bellek-sismesi-1108

2026-11-08 Gaia EP02-06: kopru (documentary_native_bridge) 17:24-20:55 arasi private 12,2 GB / WS 5,2 GB (paging). Bos RAM 1,3 GB -> MemoryGate butcesi ~0; light job'lar 0,5 sn yoklamayla adaletsiz yarisiyor, EP03'un 15 iscisi talking-head taramasinda (scan_cache._single + resources.py:336 _run_light) 21 dk hic olay yazmadi (cokme degil aclik). py-spy dump --locals ile film bazli thread ayrimi yapildi. Cozum: kopruyu ayni DOCUMENTARY_* env ile yeniden baslat (cwd C:\\Users\\meteh\\.gemini\\scripts); drive.py wait_health ile 3 sn'de yeniden POST etti, bitmis cekimler onbellekten. Bos RAM 1,3 -> 4,9 GB. Dify/LobeChat docker konteynerleri durdurmak ~2,4 GB daha verdi. Uzun partide kopru private >8 GB olunca yeniden baslatmayi dusun.
