---
tur: ders
aciklama: Disk dolunca once bunlar
kaynak: temizlik 2026-11-05; disk taramasi 2026-11-07; sohbet 11-07; sohbet 2026-11-07 gece; temizlik 2026-11-09; temizlik 2026-11-10
olusturma: 2026-11-05
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# disk-temizligi

Disk dolunca once (5 Kas temizligi: C bos 124 -> 176 GB):
- `AppData\Local\Microsoft\OneDrive\logs\ListSync`: 27,8 GB log birikmisti, dogrudan silinir.
- Temp'te 2 gunden eski dosyalar ~9 GB (`Temp\claude`, hyperframes-extract-cache).
- `uv cache clean` az yer acar (dosyalar venv'lerle hardlink).
- HF modelleri: `hf cache ls` / `hf cache rm model/<id> -y`. Uretimde kalacaklar: chatterbox-turbo (Jeff), pocket-tts, faster-whisper (large-v3, small.en), SigLIP2 (OmniVoice yalniz dub icindi, 11-10 silindi). `testbench\voiceclone_1031\engines\chatterbox\.venv` URETIMDE kullanilir, silme.
- Dokunma: Docker WSL (SearXNG), Codex pnpm deposu, Chrome. Teslim edilen filmler (Desktop\Channells) Drive'a yuklenince silinir (Desktop OneDrive'da, cop kutusuna da duser).

## 2026-11-07 (claude)

7 Kas olcumu (C bos 130 GB): pagefile.sys 41 GB (Windows otomatik yonetiyor, en yuksek kullanim 14 GB, 4 Kas'tan beri yeniden baslatma yok; yeniden baslatinca kuculur). Docker WSL docker_data.vhdx 18,4 GB (yalniz SearXNG; vhdx kendiliginden kuculmez, wsl --shutdown + Optimize-VHD/diskpart compact gerekir). yt_cache AppData\Local\documentary_materials 19 GB, hepsi son 3 gunun filmleri; Claude paketinin LocalCache\Local\documentary_materials yolu MSIX yonlendirmesiyle AYNI klasor, taramada iki kez sayilir. Bitmemis filmlerin CodexOutputs\EP*\03_materials klasorleri ~18 GB, teslimden once silinmez. Chrome OptGuideOnDeviceModel 4 GB (Chrome'un cihaz ici AI modeli). Tarama araci testbench\diskscan\scan.py (C: tamami 110 sn).

## 2026-11-07 (claude)

11-07: ytmarket_run/editscan altındaki v/ klasörleri (indirilmiş kaynak videolar, 3,5 GB) ve deep/_tmp silindi; clips/ ve state.db sayfa yeniden üretimi için tutuldu. Örnek değişirse videolar yt_gate ile yeniden iner.

## 2026-11-07 (claude)

7 Kas gece temizligi (C bos 85 -> 137 GB): test kopyalarindaki .claude/worktrees venv kopyalari 3,7 GB, test medyasi 5,1, biten filmlerin CodexOutputs+sf work 8,9, Channells teslimleri 5,5, yeniden baslatma ~12, Temp 8,5, yt_cache 13, sopro 0,6. Disk tarayicisinin gosterdigi 'AppData\Local\Packages\Claude_*\LocalCache\Local' ayri veri DEGIL: Claude uygulamasinin AppData\Local'i paket yolundan gostermesi (documentary_materials yt_cache + token_table_*.bin); iki kez sayma. hf cache gercek boyutu 15 GB, cogu uretim. docker system prune -a YAPMA (SearXNG imaji gider). Pagefile'i 8-12 GB'ye sabitleme (16 GB RAM, ffmpeg+chrome tepe). Kullanici karari: Riot Games 46,7 GB, powercfg -h off 6,3 GB, Chrome cihaz ici AI 4 GB.

## 2026-11-09 (claude)

2026-11-09 temizlik (C bos 20,7 -> 89,6 GB): GaiaTrace EP02-06 03_materials/sources ham indirmeleri 85,7 GB (EP02 14,7, EP03 19,4, EP04 17,2, EP05 16,7, EP06 17,8; source_recovery bos), EP03_Nepal+EP01_HOOK sources 1,4, yt_cache >12 saat 0,3, testbench eski medya 0,2, pip cache ~0, Temp ~0. Cop kutusu bos. Eski 6 documentary_materials/.claude/worktrees (temiz, 10/24-27) git worktree remove izin siniflandiricisinca reddedildi, duruyor. Ham sources en buyuk kalem: film teslim edilince hemen sil.

## 2026-11-10 (claude)

2026-11-10 temizlik (C bos 19 -> 207 GB, kullanici her seyi Drive'a attigini soyledi): testbench/outputs A/B filmleri (EP_A*/B*, DIFF_*_A1/B1, GPT_A, MINI_PKG; DIFF_MINI referans kaldi) ~31, darbogaz_1109 medyasi 12,1 (diff/md/py/json kaldi), dub_1101+dub_1107 12,5 (OmniVoice venv; prod OmniVoice kullanmiyor, HF OmniVoice + whisper-large-v3-turbo da silindi), cop kutusu 16, GaiaTrace EP01-06 03_materials/05_finish/chunks ~40 (TheWildYear ZIP'leri Drive'da), yt_cache full/storyboard/windows ~20, Downloads TheWildYear zip 15,8 + Video dublaj 1,5, Kanallar/Dag bitmis mp4'ler 5,2, G-Labs output/webhook 8, hyperframes history 4,7, Chrome OptGuide 4, xtts 1,9, wildyear_1110/work 2, editscan deep50/v 1,8. Kalanlar: Docker vhdx 21 (compact gerekir), Downloads/Compressed/Survival 8,8 (Survival oturumunun girdisi), voiceclone_1031 chatterbox venv (prod Jeff). Not: rm -rf icinde cd+goreli glob veya $degisken guvenlik kontrolune takilir; tam yol yaz. Bash /tmp Python'a Windows Temp olarak gorunmez.
