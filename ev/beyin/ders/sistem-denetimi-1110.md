---
tur: ders
aciklama: 5 sistem denetimi (asama3, teslim, LLM, makine, hiz): prod'a alinmamis kabul yamalari, donma kapisi 3 sn kor noktasi, klip sesi bed'i, acik oncelik listesi
kaynak: testbench/analiz_1110/*/RAPOR.md
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# sistem-denetimi-1110

2026-11-10 denetim (raporlar testbench/analiz_1110/{stage3,teslim,llm,makine,hiz}/RAPOR.md). KODDA DOGRULANDI: (1) prod documentary_materials son commit a86e941 8 Kas; 9 Kas'ta kabul edilen asama 3 yamalari (darbogaz_1109/S14_merge_prep/merged.diff: S2 restart 1154->1 sn, S6 SigLIP idle) prod'da YOK. (2) model_memory.py:180 IDLE_RELEASE_SECONDS=600 -> S6 olcumu 3 yeniden yuklemede +4,4 GB private; DOCUMENTARY_SIGLIP_IDLE_RELEASE_S=0 ile duz 3,77 GB. (3) Uretim donma kapisi freezedetect d=3.0 (runner.py:3059, window_index.py:101), yalniz VIDEO kategorisi; teslimde bulunan donmalarin cogu <3 sn -> kor nokta; gaia_finish extend/detitle ciktisinda ve final filmde donma taramasi yok. (4) Klip sesi mikse gaia_finish.py:728 'mix = vo + bed*env' ile giriyor (bosluklarda -8 dB acik). (5) drive.py reaudit() icerik hatasinda da ayni sesi 3 kez yeniden denetliyor (Gaia EP03 ~1526 sn bosa). (6) precheck Flash-low zaten prod'da (io.py:796, uyum %97, %100 degil). UYGULANDI: Kanallar/preflight.py artik preflight_ek.py'yi de kosar (commit limiti, disk esigi, yetim surec, IObit; +4 sn). HAZIR AMA UYGULANMADI (test/onay ister): teslim_kapisi.py (donma d=0.8, bosluk RMS, sure, segment; yalniz sentetik filmde denendi), hiz/drive_reaudit_content_fail.diff, stage3/siglip_idle_release_off.diff, llm/P1-P6 diff (reasoning_effort'suz Flash: SkullStudio pipeline/common.py:89 ana nokta). ZAYIF KANIT, ALMA: selector cap (B kolunda baska bayraklar da acik, sure kazanci yok), S12 bant dedektoru 47/47 iddiasi, S13 yuz taramasi (PASS ornegi yok). Commit limiti 37,6 GB (pagefile kuculmus): 3 paralel film tepe yapabilir.
