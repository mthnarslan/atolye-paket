---
tur: ders
aciklama: 10 film/2 oturum kapasite tavanlari (G-Labs 1930 sn, GPT review 920 sn, HF render 770 sn/film); VOICE kilidi sentez disini da kapatiyor; early ANIM havuzu skorlama fallback'inde atlaniyor; precheck Flash-low'a (replay %97), review GPT'de kalir (%70, %21-29 yanlis gecis); SearXNG ilk sorgu 0 sonuc -> bos foto havuzu -> 'No feasible allocation'
kaynak: testbench/sched_1106/PLAN.md; testbench/sched_1106/PLAN.md; testbench/judge_flash_1106/REPORT.md
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# zamanlama-10-film-tavanlari-1106

testbench/sched_1106 (timeline.py, gptq.py, sim.py, PLAN.md). EP04/EP05 1106: GPT governor codex limit 4 iken film basi 42-46 istek kuyrukta 60 sn'de oluyor, 56-65 codex hatasi, cooldown 900-2400 sn; GPT_SLOTS=8 + FLASH_TO_GPT=1 ile precheck'ler GPT'ye akiyor (115-161/film), review tasmasi Flash'a hic dusmuyor. Flash 15 slotun 0.7'si dolu, a1/VDS stage 3'te bos, G-Labs sadece son 10 dk'da dolu. judge_flash_1106 ara sonuc: precheck Flash-low n=16 %100 uyum 6 sn (GPT 37 sn); review Flash %72 uyum, %31 yanlis red -> review GPT'de kalsin. Sim: 10 film mevcut 404 dk, oneri 358 dk (G-Labs tavan %90), ANIM 20->10 veya G-Labs 3->6 ile 205 dk (GPT tavan). Tek film gecikmesi ~60 dk; 10 dk/film hedefi ancak tavan degisikligiyle (kullanici karari). Duzeltmeler: fullrun VOICE slotu master_voiceover.wav yazilinca birak (fullrun_voice_release.diff, test gecti), bridge env GPT_SLOTS=4 FLASH_TO_GPT=0, profil codex 12->4, governor oncelik (review>judge>precheck), early3d skorlama 1 kez yeniden dene, anim.py'de surecler arasi 3'lu G-Labs kilidi.

## 2026-11-06 (claude)

Guncelleme: judge_flash_1106/REPORT.md kesin sonuc: precheck Flash-low %97 uyum, 0/4 yanlis gecis, 6 sn (GPT 37 sn) -> io.py ~768'de precheck her zaman flash; review Flash %70 uyum, %21-29 yanlis GECIS -> GPT'de tam 4 eszamanli kalir. EP02 stage 3: SearXNG baslik sorgusu 15:25'te 200 + 0 sonuc (timeout degil, mevcut retry calismadi), 15:33'te ayni sorgu 73 -> bos foto havuzu -> planning.py:1425 'No feasible allocation', film 2 kez dustu, foto elle eklendi. Onerilen: sources.py:884 count==0'da 20 sn sonra 1 tekrar + kisa yedek sorgu, ensure_searxng stage-3 basinda; oran koruyucu degismez. Ayrintilar testbench/sched_1106/PLAN.md.
