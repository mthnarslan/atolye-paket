---
tur: konu
aciklama: 3D render tavanı 5'tir ve yükseltilemez: 4'te 2/4, 5'te 4/5, 6'da 3/6 render bozuk çıkıyor.
kaynak: auto-memory C--Users-meteh/memory/documentary-3d-render-ceiling.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
**Ölçüm (2026-10-21, `tmp/bench_hyperframes.py`):** Gerçek `three_render.render_three` ile, 75 karelik aynı 3D proje, eşzamanlılık seviyelerinde:

| Eşzamanlılık | Duvar süresi | Başarılı | Hata |
|---|---|---|---|
| 1 | 13.9 sn | 1/1 | — |
| 2 | 16.5 sn | 2/2 | — |
| 3 | 11.7 sn | 3/3 | — |
| 4 | 22.3 sn | **2/4** | `Warm WebGL render failed: Error: write EOF` |
| 5 | 13.1 sn | **4/5** | `write EOF` |
| 6 | 186.3 sn | **3/6** | `write EOF`, `TimeoutError: Warm browser operation timed out`, `OSError [Errno 22]` |

**Sonuç:** `system_speed_profile.json`'daki `hardware.channels.hyperframes.concurrency = 5` **ölçümle doğru** ve **yükseltilmemeli**. 4-5 arası bir tarayıcı havuzu birbirinin belleğini/gpu'sunu ezdiği için Chromium süreci "write EOF" ile ölüyor. 6'da ayrıca 186 sn'lik timeout çıkıyor.

**Neden önemli:** Canlı koşumun en yavaş worker'ları 3D render'da (shot 31: 646 sn'in 624 sn'i render). Teşhis raporu "hyperframes tavanı 5'i 12'ye çıkar" diye öneriyordu — **bu öneri yanlış**, kaliteyi (bozuk dosya) bozuyor. Render tarafında kazanç aramak yerine tarama (hook) ve çift koşu tarafına bakmak gerekir.

**How to apply:** Bir tavanı "daha çok paralellik" ile yükseltmeden önce ölç ve **çıktı geçerliliğini** de kontrol et. Hız kazancı bozuk dosyayla geliyorsa kazanç değildir. İlgili: [[documentary-20min-budget]], [[documentary-bridge-bypass-and-hot-reload]].

Olcum eski HyperFrames yolunda yapildi; fastrender (239a954) sonrasi yeniden olculmedi.
