---
tur: ders
aciklama: RAM denetimi 15 Kas (3. tur R7-R13 eklendi)
kaynak: testbench/ram_1115; testbench/ram_1115/R7..R13
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# ram-denetim-1115

testbench/ram_1115 R1-R6 (GPT iscileri, kanitlar kontrol edildi). R1: ORB kosularinda lowmem anlarinda ffmpeg ort RSS 434 MB (286 gozlem), MemoryGate per_unit_mb=300 -> kapi fazla paralellik veriyor; B1 228 sn <1500 MB. Python (kopru) ort 1933 MB. R2: lazy import kazanci 12,7 MB (onemsiz). R3: SigLIP prod RSS 1960 MB, VRAM 743 MB; isci 'safetensors mmap -763 MB' dedi ama metin yolu test edilmemis, kod hatali -> gecersiz (R3b yeniden). R4: Chrome --single-process 8 MB kazanc, +1 sn: degmez. R5: Pocket PC RSS 924 MB, RTF 0,30-0,33; A1'de ses klonlama agirligi HF yetkisi yuzunden inmedi (R5b: PC HF cache'ini kopyala). R6: bosta kapatilabilir Antigravity 609, Chrome 548, Phone Link 152 MB.


**2. tur (kanıt kontrol edildi):** R3b: SigLIP ağırlıkları zaten GPU'da (görsel 186 MB + metin 171 MB, token tablosu 0); köprüdeki ~1,6-2,1 GB RSS torch/CUDA çalışma zamanı. mmap/bf16/GPU varyantları RSS düşürmüyor (image_gpu_text_cpu +950 MB). Tek yol SigLIP'i ayrı sürece/makineye almak (mimari, konsey gerekir). Aynı prod iki taze süreçte skor farkı 0,004 (GPU nondeterminizm), top-5 aynı. R5b: A1'de Pocket PC HF önbelleği kopyalanınca offline çalışıyor (HF_HUB_OFFLINE=1, ~/.cache/huggingface), PC'den 2,2-2,6x yavaş (RTF 0,80-0,95), RSS ~880-1000 MB; AMA 3 cümleden 1'i iki koşuda da bozuk ('reflected across the water' -> 'a cresting matter'/'a crash together'), PC'de WER 0. Prod'a yedek işçi olarak alınmaz; ARM sayısal fark şüphesi, daha çok cümleyle tekrar gerek.

## 2026-11-15 (claude)

**3. tur (Claude ajanlari, kanit kontrol edildi):**
- **R7 SigLIP bosta kirpma:** tipli EmptyWorkingSet, DOCUMENTARY_SIGLIP_IDLE_TRIM_S=60; bosta RSS 1419 -> 4 MB, skor kaymasi (0,0069) kirpmasiz kontrolde de var. Yama ram_1115/R7_eprime/yama.diff, prod'a alinmadi. Film A/B (R13_film_ab, run_one.py + bridge_up.ps1) Flash 503 yuzunden kosmadi. testbench/scripts prod HEAD 9769e83'e esitlendi; ust dizindeki testbench/scripts/documentary_native_bridge.py prod'dan eski.
- **R11 kart render:** cards.render_project her karta ayri node+chrome aciyor. fastrender.mjs --par N (tek browser) + --renderer-process-limit=1 ile N=4 toplam RSS 2460 -> 1422 MB (-%42), PSNR >=59 dB. Kuyruk degisikligi gerekiyor, prod'a alinmadi.
- **R9 ffmpeg:** 434 MB = 4K kaynakli render (1080p 251, 4K 470 MB). Kaliteyi koruyan ayar en iyi -%26 ve 2x yavas. Footage taramasi CPU decode -threads 4 -filter_threads 1: 176 -> 72 MB. Cozum: 4K'yi once 1080p'ye indirmek ya da kapida 4K'yi 480 MB saymak.
- **R12 kapi:** heavy ffmpeg gercekte medyan 444, maks 1371 MB (kapi 300 diyor). Darbogaz asama 3, 3 film paralel kesimde (bos RAM 195 MB'a iniyor). Ogrenen kapi yamasi (son 20 isin medyani) R12_kapi/yama.diff, test 6/6.
- **R10 Pocket bosta kirpma:** RSS 460 -> 0,1 MB, sonraki cumle +0,15 sn, WAV farki float gurultusu (SNR 125 dB). MemoryGate available'a yansimadi (paralel gurultu).
- **R8 Blender:** tek surec RSS 745 MB / private 2,5 GB. 6 shot tek surecte sirayla 1,03 GB 422 sn; 2 paralel 4,4 GB 390 sn; 3 paralel private 8,2 GB 536 sn. Tek surecte sirali calistirmak RAM'i ~4x dusuruyor, sure ~%8 uzuyor. factory-startup/noaudio 0 kazanc. 16 GB'ta en fazla 2.
