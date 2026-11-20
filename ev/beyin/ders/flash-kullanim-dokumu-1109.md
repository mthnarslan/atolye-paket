---
tur: ders
aciklama: Flash istek dokumu 7-9 Kas: en buyuk israf codex iscilerinin Flash-high'da kosmasi (~350M token/gun, kapatildi); asama 3 cekim basina 3 Flash (grid+secim+precheck), onarim+autoresume tekrarlari %43
kaynak: testbench/flash_tasarruf_1109; Engineered tools/drive.py:45; runner.py:2782,5405
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# flash-kullanim-dokumu-1109

Olcum (events.jsonl, request_id ile tekillestirilmis, 7-9 Kas): boru hatti 20533 Flash istegi. prod: shots 11154 (1658 cekim, p50 6/cekim, p90 13, max 26), sentence_finder 1640, inventory 1537 (grup basina 1), storyboards 1501 (kaynak video basina 1), pinpoint 443, source_recovery 394. Cekim ici: grid_prefilter 3601, secim (flash.requests) 3716, precheck 2738, hata 667 (cogu HTTP 500 9router), review'in Flash'a dusen kismi ~430. Seviye: base 6340, repair_1 2397, repair_2 939, repair_3 1478; 504 cekim repair_3'e kadar gitti. Autoresume (Engineered drive.py set_aside_unresolved) cozulemeyen cekimi tum zinciriyle yeniden kosar: 2399 istek (%21) sonraki kosulardan. grid_prefilter onbellegi repair_N klasoru basina ve 9 panelin tamamina bagli -> reddedilen aday cikinca ayni adaylar yeniden sorulur (~1950 tekrar). Codex iscileri (run.sh/auto.sh flash) 9 Kas'ta Flash-high ile ~350M token yakti: darbogaz_1109 run.sh artik ALLOW_FLASH_AGENT olmadan Flash ajan acmaz, auto.sh flash swap kapali. SkullStudio Flash'i neredeyse hic kullanmiyor. Hedge %0,3 onemsiz. Sayim betigi: CodexOutputs/<film>/03_materials/**/events.jsonl, stage=api_request_started role=flash, kazanan tur api_race_winner.physical_receipts klasor adindan.
