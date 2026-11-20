# Argon (Gemini, yüksek effort) mimari analizi: 26 Ekim 2026

Bu belge, Argon'a verilen soru ve cevabının özetidir. Soruda sistemin bütün aşamaları, donanım, 26 Ekim ölçümleri ve günde 40 film hedefi anlatıldı. Argon'un iddiaları bizim ölçümlerimizle karşılaştırılarak not edildi.

## Teşhis
- Darboğaz LLM değil, GPU'nun encode kapasitesi de değil. Asıl darboğaz, ffmpeg ve analiz işlerinin RAM kapısında sıraya girip sahne başına ortalama ~90 sn beklemesi.
  - *Bizim düzeltmemiz:* Kapı, çalışan işleri iki kez sayıyordu ve hafif işleri ağır sayıyordu. Bu, `f5b8e13` commit'inde düzeltildi.
- Windows'ta `import torch` + CUDA, süreç başına 1,8–2,5 GB commit yaratıyor. Hesap: OS ~3,5 + TTS 3,7 + köprü 7,3 GB ≈ 14,5 GB commit.
- Tek süreçte thread'ler iki sorun yaratıyor:
  - Bellek ayırıcıları belleği sisteme geri vermiyor.
  - OpenBLAS/OpenMP/OpenCV her çekirdek için thread açıyor; CPU %100'e kilitleniyor.
- 4 GB VRAM'i aşınca Windows (WDDM) GPU belleğini sistem RAM'ine taşıyor. Bu TTS'i zaman aşımına düşürüyor.
  - *Bizim ölçümümüz:* GPU 3,6/4 GB doluydu ve TTS açılışı zaman aşımına düştü.

## 40 film/gün kapasite hesabı
40 film/gün = saatte 1,67 film = film başına ~200 sahne → saatte 333 kabul edilmiş sahne.

| Kalem | Şu anki oranla | Hedef oranla | Not |
|---|---|---|---|
| Render/sahne | 1,62 | 1,25 | |
| Saatte render | 540 | 417 | 5,5 sn klip NVENC ~1,2 sn → GPU'nun ~%18'i |
| Flash çağrısı/saat | 540 | 333 | ~1,2 eşzamanlı istek yeter |
| GPT çağrısı/saat | 540 | 333 | ~2,7 eşzamanlı istek (4–6 limit yeterli) |
| TTS | ~700 dk ses/gün | | saatte ~32 dk |
| İndirme | 120–280 GB/gün | 45–70 GB/gün | ortak önbellekle |
| Disk yazma | | | ~250–350 GB/gün |

**Sonuç:** 4 GB GPU 40/gün için fiziksel olarak yeterli; sistemi durduran süreç mimarisi ve bellek yönetimi.

## Hedef mimari
Kalıcı durumlu iş kuyruğu + izole uzman işçiler:

- **Orkestratör:** PostgreSQL + Redis + Dramatiq (ya da Temporal).
  - Her sahne bir durum makinesi: PENDING → CANDIDATES → PRECHECKED → RENDERED → APPROVED.
  - Kaynak kuralları (4 kullanım, 30 sn ara) veritabanında atomik rezervasyonla (`SELECT ... FOR UPDATE`) yönetiliyor.
- **Ortak model sunucusu (tek süreç, torch yok):**
  - onnxruntime-gpu; alternatifler Triton ya da michaelfeil/infinity.
  - SigLIP2 FP16/INT8 ONNX ya da MobileCLIP-S2 (~350–600 MB VRAM).
  - YuNet ONNX.
  - Ayarlar: `gpu_mem_limit` = 1 GB, `arena_extend_strategy` = kSameAsRequested.
  - Diğer işçiler torch yüklemiyor; kareyi bu sunucuya gönderip skor alıyor.
- **Vektör/katalog:** Qdrant (mmap ile ~150 MB RAM) ya da pgvector.
- **TTS + ASR işçisi:**
  - Mevcut TTS kalacaksa toplu çalışma, iş bitince unload.
  - Daha hafif seçenekler: kendi anlatıcı sesine fine-tune edilmiş GPT-SoVITS v2, Kokoro-82M (500 MB'ın altında VRAM, gerçek zamanın 15 katı hızlı), Piper/VITS (CPU'da gerçek zamanın 20 katı hızlı, GPU kullanmıyor).
  - ASR: faster-whisper INT8.
- **İndirme işçileri:** asyncio + yt-dlp/aria2c (~45 MB RAM).
- **Ön analiz işçileri (2 adet):** PyAV ile 360p bellek içi decode, sahne kesimi, donma, altyazı, ardından model sunucusuna sorgu.
- **Render işçileri (2 sabit slot):** NVENC.
- **Paketleme:** `-c copy` birleştirme.

**Neyin nerede çalışacağı:**
- **Linux VDS:** orkestratör, veritabanı, Qdrant, LLM işçileri, arama.
- **Windows PC:** model sunucusu, TTS/ASR, indirme, ön analiz, render, paketleme. Hedef toplam ~7,5 GB RAM ve ~2,6 GB VRAM.
- **Kiralık GPU:** Gerekli değil. Ağır TTS kalırsa günde ~2 saatlik spot GPU (~$0,40/gün) kullanılabilir.

## RAM'i düşürmenin somut yolları
1. **torch'u izole etmek:** Ana süreçten torch'u çıkarıp tek bir ONNX model sunucusu kullanmak. Kazanç ~4,5 GB commit.
2. **Thread disiplini:** Her işçide numpy/cv2 import edilmeden önce `OMP_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2`, `MKL_NUM_THREADS=2` ve `cv2.setNumThreads(1)`. Kazanç ~600 MB RAM ve %30 CPU.
3. **Hafif ön analiz:** 360p streaming decode, sadece gereken kareler (PyAV generator).
4. **ffmpeg:**
   - NVDEC kullanılmamalı.
   - `-ss/-to` parametreleri `-i`'den önce yazılmalı.
   - NVENC için `-rc-lookahead 0 -surfaces 4`.
   - `-vf fps=25`, `-video_track_timescale 12800`, `-an`.
5. **TTS:** Ses aşaması bitince modeli unload etmek.
   - *Bizim tecrübemiz:* Dolu GPU'da soğuk açılış dakikalar sürüyor. Bu yüzden ses bekleyen film varken servis açık tutuluyor.

## Boşa işi azaltma
1. **Render öncesi sanal kontak sayfası ve top-3 seçim (en büyük kaldıraç):**
   - En iyi 3 adayın 360p karelerinden tek bir birleşik JPEG yapılıyor; tek bir Flash çağrısı seçim ve ön kontrolü birlikte yapıyor.
   - Sadece 1. aday render ediliyor ve GPT'ye gidiyor. GPT reddederse 2. aday hemen render ediliyor.
   - Beklenen etki: kabul oranı %44'ten %82–88'e çıkar; render %55, LLM çağrısı %35 azalır.
   - *Bizde:* Ön kontrol artık render'dan önce (`cecb3a7`). Top-3 tek çağrı henüz yok.
2. **Kaynakların bir kez indekslenmesi:**
   - Her 32 sn'lik pencere indirildiği anda kesimsiz alt aralıklara bölünüyor.
   - Her alt aralığın yüz, donma, hareket, altyazı bilgisi ve 2 sn'de bir SigLIP vektörü veritabanına yazılıyor.
   - Sahne adayı aranırken video bir daha açılmıyor.
   - *Bizde:* `window_index.py` kısmen bunu yapıyor.
3. **Filmler arası küresel önbellek:** İndirilen pencereler `SHA1(source_id+start)` adıyla merkezi bir havuzda tutuluyor; analizler ortak kullanılıyor.
4. **Güvene dayalı GPT incelemesi:** SigLIP en üst %25'te, uyarısız ve Flash yüksek güvenle geçtiyse GPT incelemesi atlanıyor. GPT sadece sınırdaki sahnelerde hakem.
   - *Not:* Kalite kuralı açısından dikkat gerektirir.

## Argon'un sıralı geçiş planı
| Faz | İş | Süre | Beklenen kapasite |
|---|---|---|---|
| 1 | Thread disiplini, ffmpeg bayrakları, TTS unload | 2–3 saat | 15–18 film/gün |
| 2 | Ayrı ONNX model sunucusu, köprüden torch'un çıkarılması | 1 gün | 25–28 film/gün |
| 3 | Sanal kontak sayfası + top-3 Flash seçimi | 1–2 gün | 38–42 film/gün |
| 4 | Kalıcı alt klip kataloğu + küresel önbellek | 2 gün | CPU %50–65'e iner, indirme %60 düşer |
| 5 | Orkestrasyon ve LLM işçilerinin VDS'ye taşınması | 2–3 gün | 50+ film/gün |

## Yapmayacakları
- Windows'ta Docker/WSL2 kullanmak: vmmem 4–8 GB yer.
  - *Bizde:* Docker yalnızca SearXNG için çalışıyor; hayvan filmlerinde gerekmiyor.
- 4 GB kartta NVDEC kullanmak.
- Son birleştirmede yeniden encode etmek.
- Kafka/Kubernetes/Ray'e geçmek: PostgreSQL + Redis + Dramatiq yeterli.

## Riskler
- **`-c copy` birleştirmede DTS kayması:** Sahnelerde `fps=25`, sabit timescale ve sessiz klipler gerekiyor.
- **Paralel kaynak kuralı ihlali:** Veritabanında rezervasyon gerekiyor.
- **Küçük altyazıları Flash'ın kaçırması:** Deterministik altyazı tespiti gerekiyor (Sobel kenar yoğunluğu ya da PaddleOCR-mobile).
