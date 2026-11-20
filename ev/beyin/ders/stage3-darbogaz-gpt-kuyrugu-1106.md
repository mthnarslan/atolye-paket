---
tur: ders
aciklama: Stage 3 suresinin ~%70'i LLM bekleme: GPT/review kanali (limit 4, tavan 12) ort. 72 sn kuyruk + 120-430 sn gpt-6-sol; yerel CPU sadece ~%7, a1'e kesim tasimak kazandirmaz
kaynak: testbench/offload_stage3_1106/BREAKDOWN.md
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# stage3-darbogaz-gpt-kuyrugu-1106

EP05 1106 olcumu (testbench/offload_stage3_1106/BREAKDOWN.md): stage 3 72 dk; kuyruk oncesi ~620 sn tamamen YouTube/Flash/GPT bekleme; 44 dk cekim fazinda GPT kanali 93 istek, ort. kuyruk 72 sn (6728 sn), grid_prefilter ort 56 sn medyan 15 sn kuyruk 290-430 sn (tek gpt-6-sol cagrisi), precheck_before_render 38 sn. Flash 15 slot doymuyor (kuyruk 2 sn). Saf render 8 sn ort, tum CPU adimlari ~3350/44000 isci-sn: sifira insa ~3 dk (%4). ANIM kuyrugu: G-Labs anim_make 15 x ~327 sn (<=3 paralel). Tailscale 6 Kas 15:15 saglikli (ping 33 ms, 3 MB 2,3 sn = acik IP ile ayni), yani GPT yavasligi hattin degil modelin/servisin. Kaldiraclar: GPT kanal limiti ve gecikmesi (VDS servisine dokunma), DOCUMENTARY_FLASH_TO_GPT=0 / precheck'i Flash'a (hakem degisikligi: judgeprobe + kullanici onayi + testbench A/B), ANIM sayisi. a1 kullanim: ASR yedegi (/opt/offload, 669 sn ses 103 sn, 0,8 GB) ve V3 render.
