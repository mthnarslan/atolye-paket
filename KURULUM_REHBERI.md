# Belgesel hattı: sıfırdan kurulum ve ilk 5 film

> **Bu dosya Claude Code'a verilmek için yazıldı.** Kendi bilgisayarında Claude Code'u aç, bu repoyu klonladığın klasörde başlat ve şunu yaz:
> *"KURULUM_REHBERI.md'yi baştan sona uygula. Her adımın sonundaki KONTROL'ü koş, geçmeden sonrakine geçme. Hesap girişleri ve şifreler bende, o adımlarda beni bekle."*

Bu paket, üretim makinesindeki belgesel hattının (ENGINEERED / vahşi yaşam) bütün kodunu taşır: köprü, aşamalar, ortak beyin (`beyin/`, geçmişte çözülmüş yüzlerce hata ve kural), kurallar (`Kanallar/SISTEM.md`), Claude hook'ları ve ajanları. **Taşımadığı şeyler:** hesaplar, çerezler, API anahtarları, ses referansı, eski filmler. Bunları her makine kendisi kurar, kimseyle paylaşmaz.

## 0. Kurallar (Claude bunlara her adımda uyar)
- Şifre, çerez, anahtar, e-posta hiçbir dosyaya, loga ya da sohbete yazılmaz. Google girişlerini kullanıcı kendi eliyle Firefox'ta yapar.
- QA eşikleri, testler, `yt_gate` ve NVENC sınırları gevşetilmez. Bir film QA'dan geçmiyorsa sebebi bulunur, hakem susturulmaz.
- 2 dakikadan uzun her iş `python Kanallar/bekci.py` ile bekçili başlatılır (bkz. `Kanallar/SISTEM.md`).
- Yeni bir işe başlamadan önce `python beyin/araclar/ara.py "konu"` ile geçmiş hatalara bakılır. Öğrenilen kalıcı bilgi `beyin/araclar/ekle.py` ile yazılır.
- Paketteki `Kanallar/SISTEM.md` üretim makinesinin durumunu anlatır. Oradaki VDS, 9router ve G-Labs kısımları bu makinede **yok**, ne kullanılacağını bu rehber söyler.

## 1. Programlar (sırayla)
| Program | Sürüm / not | KONTROL |
|---|---|---|
| Python | **3.12.x**, kullanıcıya kurulum (varsayılan yol `%LOCALAPPDATA%\Programs\Python\Python312`), "Add to PATH" işaretli | `python --version` → 3.12 |
| Git | güncel | `git --version` |
| ffmpeg | **full build** (gyan.dev "ffmpeg-release-full"), `bin` PATH'e | `ffmpeg -hide_banner -encoders \| findstr nvenc` → h264_nvenc görünmeli (NVIDIA kart varsa) |
| NVIDIA sürücüsü | güncel Game Ready/Studio | `nvidia-smi` |
| Node.js | **24.x** LTS | `node -v` |
| HyperFrames | `npm i -g hyperframes@0.8.181` (kartlar/yazılar bununla çizilir) | `npx hyperframes --version` |
| Google Chrome | normal kurulum (`C:\Program Files\Google\Chrome\Application\chrome.exe`) | dosya var |
| Firefox | normal kurulum | açılıyor |
| Docker Desktop | WSL2 ile | `docker ps` |
| Montserrat yazı tipi | Google Fonts'tan indir, "Tüm kullanıcılar için yükle" | Yazı Tipleri'nde Montserrat |

Makine: 16 GB RAM ve 4 GB GPU yeterli. **Disk:** film başına ~5,4 GB ara dosya çıkar, 5 film için en az **40 GB boş** olsun.

## 2. Paketi yerleştir
```
git clone <repo-adresi> %USERPROFILE%\atolye-paket
cd %USERPROFILE%\atolye-paket
python kur.py --kuru      (ne yapacağını gösterir)
python kur.py             (kurar)
```
`kur.py` şunları yapar:
- `ev/` altındaki her şeyi kullanıcı klasörüne kopyalar ve `C:\Users\meteh` yollarını bu makinenin yoluna çevirir.
- Claude hook'larını `~/.claude/settings.json` içine yazar. Eski dosya `.kur_yedek` olarak saklanır.
- Çalışma klasörlerini açar.
- Eksik ortam değişkenlerini yazar.

**KONTROL:** yeni bir terminal aç, `echo %DOCUMENTARY_VOICE_ENGINE%` → `pocket`. Claude Code'u yeniden başlat ki hook'lar yüklensin.

**Güncelleme (sonradan):** `git pull` ve ardından `python kur.py`. Elle değiştirdiğin dosyalar ezilmez, "ÇAKIŞMA" diye listelenir. Claude bunları tek tek birleştirir.

## 3. Ana Python paketleri (global Python 3.12)
`faster_whisper` ve `rembg` hat tarafından **global** Python ile çağrılır, o yüzden ana ortam venv değildir:
```
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install -r %USERPROFILE%\atolye-paket\requirements.txt
```
NVIDIA kart yoksa torch'u `--index-url https://download.pytorch.org/whl/cpu` ile kur. Çok yavaş olur ama çalışır.
**KONTROL:** `python -c "import torch,faster_whisper,rembg,open_clip,cv2;print(torch.cuda.is_available())"` → `True` (NVIDIA varsa).
Bir modül eksik çıkarsa (`ModuleNotFoundError`), Claude onu pip ile kurar ve `requirements.txt`'ye ekler.

## 4. Servisler
Hepsi kendi terminalinde ya da arka planda koşar. Bilgisayar yeniden açılınca 4.1–4.5 tekrar başlatılır.

### 4.1 Gemini (gemweb, :8790): planlama, hakem, görsel kontrol. **ZORUNLU**
Bu makinenin kendi Google hesaplarıyla çalışır, üretim makinesinin hesaplarıyla hiçbir bağı yoktur.
1. Venv:
   ```
   cd %USERPROFILE%\testbench\gemweb_1116
   python -m venv .venv
   .venv\Scripts\pip install gemini-webapi==2.1.1 fastapi uvicorn curl_cffi loguru orjson pydantic
   ```
2. **Hesaplar (kullanıcı yapar):** Firefox'ta `about:profiles` → "Yeni profil oluştur" (ör. `gem1`). O profille Firefox'u aç ve gemini.google.com'a kendi Gmail'inle gir.
   - Aynı profilde "Hesap ekle" ile birden fazla Gmail açılabilir. Bunlar /u/0, /u/1 … olarak sıralanır.
   - Profil klasörünün adı `about:profiles` → "Kök Dizin" satırının son parçasıdır (ör. `ab12cd34.gem1`).
3. Hangi hesap hangi sırada:
   ```
   .venv\Scripts\python hesap_bul.py <profil-klasoru>
   ```
   Her satır bir hesaptır (0, 1, 2 …).
4. Her hesap için `hesaplar\<kisa-ad>.json` dosyası yaz: `{"firefox": "<profil-klasoru>", "u": 0}`. İkinci hesap için `"u": 1` olur, ve böyle devam eder. Bu klasör hiçbir zaman git'e girmez.
5. Başlat:
   ```
   .venv\Scripts\python nobetci.py
   ```
   Panel: http://127.0.0.1:8790/

**KONTROL:** panelde hesaplar "hazır" görünür. Ardından:
```
python -c "import sys;sys.path.insert(0,r'%USERPROFILE%\Kanallar');import gemweb;print(gemweb.sor('2+2?'))"
```
Ayrıntı: `Kanallar/gemweb_kullanim.md`. Hesap başına 5 saatte ~210 istek hakkı vardır. Bir film ~150–300 istek yer, 5 film için **en az 5–6 hesap** gerekir. Model hep `gemini-4-hydrogen`.

### 4.2 Pocket TTS (:7863): anlatıcı sesi. **ZORUNLU**
```
cd %USERPROFILE%\codex-repo-tests\voice-lab\pocket-tts
python -m venv .venv
.venv\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\pip install pocket-tts==4.0.1 soundfile psutil numpy
powershell -File ..\Start-Pocket.ps1
```
- İlk açılışta model indirilir, birkaç dakika sürer.
- `pocket_server.log.err`'de eksik modül çıkarsa Claude onu kurar.
- **Ses referansı:** kendi anlatıcının 10–20 sn'lik temiz kaydı (wav, tek kişi, müziksiz) → `%USERPROFILE%\voices\anlatici.wav`, ardından `setx DOCUMENTARY_VOICE_REF %USERPROFILE%\voices\anlatici.wav`.

**KONTROL:** `curl http://127.0.0.1:7863/` cevap verir.

### 4.3 GPT (planlama ve hakem rolleri). **ZORUNLU**
Hat, OpenAI uyumlu bir uç bekler: `DOCUMENTARY_CODEX_ENDPOINT` (ör. `http://127.0.0.1:20128/v1`) ve model adı **`gpt-6-sol`** (`documentary_materials/.../io.py` içindeki `CODEX` sabiti).
- Kendi ChatGPT/OpenAI erişimin varsa yerelde bir OpenAI uyumlu geçit kur ve `gpt-6-sol` adını oradaki modele eşle (alias). Ya da `CODEX` sabitini oradaki model adına çevir; bu değişikliği `beyin`'e yaz.
- Anahtar Windows Kimlik Yöneticisi'nde tutulur (dosyaya yazılmaz). Kullanıcı kendisi girer:
  ```
  cmdkey /generic:Antigravity.Codex.VDS.ApiKey /user:x /pass:<anahtar>
  ```
  Sonra `setx DOCUMENTARY_CODEX_ENDPOINT <uç-adresi>`.

**KONTROL:**
```
python -c "import sys;sys.path.insert(0,r'%USERPROFILE%\.gemini\scripts');import vds_secret_store as v;print(bool(v.read_secret('codex_vds')))"
```
`True` olmalı. `False` ise `cmdkey` ile yazılan anahtarın okunuşunu (UTF-16/UTF-8) Claude `vds_secret_store.py`'de düzeltir. Sonra tek bir deneme isteği gönderilir.

### 4.4 SearXNG (:8888): görüntü/kaynak araması. **ZORUNLU**
```
docker run -d --name searxng --restart unless-stopped -p 8888:8080 searxng/searxng
```
İlk açılıştan sonra konteynerdeki `/etc/searxng/settings.yml` içinde `search: formats:` listesine `json` ekle ve `docker restart searxng` yap.
**KONTROL:** `curl "http://127.0.0.1:8888/search?q=orca&format=json"` JSON döner.

### 4.5 YouTube: Firefox oturumu + PO token sunucusu (:4416). **ZORUNLU**
- Firefox'un **varsayılan** profilinde YouTube'a gir ve açık bırak. Hat çerezleri oradan okur (`DOCUMENTARY_YT_COOKIES_BROWSER=firefox`). Gemini için açtığın profillerle karıştırma.
- PO token sunucusu: `bgutil-ytdlp-pot-provider` **2.0.2** sürümünün sunucusunu (GitHub: Brainicism/bgutil-ytdlp-pot-provider, `server/` klasörü) README'deki adımlarla derle. Çalıştırma: `node build/main.js` (port 4416). Gerekirse `setx BGUTIL_POT_SERVER http://127.0.0.1:4416`.

**KONTROL:** `python %USERPROFILE%\Kanallar\preflight.py` içinde YouTube ve PO token satırları OK.

### 4.6 G-Labs (:8765): yalnız animasyonlu çekimler, **İSTEĞE BAĞLI**
Yoksa hat ANIM çekimlerini atlar ya da gerçek görüntüyle doldurur. Kurulmaz.

### 4.7 Köprü (:8099): bütün aşamaları yürüten servis
```
cd %USERPROFILE%\.gemini\scripts
python documentary_native_bridge.py
```
Kendi terminalinde açık kalır.

## 5. Ön kontrol
```
python %USERPROFILE%\Kanallar\preflight.py
```
- **Kritik FAIL varsa film başlatılmaz.** Her FAIL satırının yanında "yapılacak" yazar.
- G-Labs ve VDS satırları bu makinede UYARI/FAIL verebilir. Kritik değillerse geç.
- Kritik oldukları hâlde bu makinede gereksizlerse, Claude `preflight.py`'de bunları bu makine için kritik dışı yapar ve `beyin`'e yazar.

## 6. Mini deneme (zorunlu, ~10–20 dk)
Paketteki 1 dakikalık örnek: `Kanallar\Engineered\ornek\WOE_SAMPLE_ENDERLIN_1MIN`
```
python %USERPROFILE%\Kanallar\bekci.py --ad mini -- python %USERPROFILE%\Kanallar\Engineered\tools\drive.py %USERPROFILE%\Kanallar\Engineered\ornek\WOE_SAMPLE_ENDERLIN_1MIN 1 4
```
- **Aşama sonuçları:** 1 = SUCCESS/PASS (ses), 2 = PASS (plan), 3 = MATERIALS_READY (görüntüler), 4 = PASS veya PASS_WITH_NOTES (render).
- **drive.py çıkış kodları:**
  - 0 = bitti
  - 1–4 = o aşama düştü
  - 10 = ağ/servis koptu (servisleri kontrol et, aynı komutu tekrar ver)
  - 11 = bu klasör için iş zaten koşuyor
  - 13 = ses denetimi yalnız Gemini ağ hatasıyla bitti, aşama 1 tekrar edilebilir
- Her düşüşte `REASON ...` satırı yazar. Claude önce `ara.py` ile bu sebebi beyinde arar.

**Çıktı:** `%USERPROFILE%\CodexOutputs\<film>\03_materials\complete_video.mp4`. Bu videoyu baştan sona izle: ses ile görüntü uyumu, logo, yazı.

## 7. Kendi 5 filmin
1. **Metin.** Her film için bir klasör (ör. `%USERPROFILE%\Filmler\EP01_ORCA`) aç. Örnek klasördeki düzeni kopyala:
   - `04_SCRIPT_EN.md`: numaralı tablo. Yalnız anlatım hücresi okunur, `[...]` içindeki notlar atılır.
   - Bilgi notu (fact sheet).
   - Referans görsel.
   - Metin yazımı için ortak atölye sitesindeki **Nasıl yapıyoruz → Metin** rehberine uy.
2. **Sırayla başlat.** İlk filmi tek koş, bitince ikinciyi başlat. Makine rahatsa en fazla 2–3 paralel çalıştır. RAM 16 GB ise 5'i birden başlatma.
   ```
   python %USERPROFILE%\Kanallar\bekci.py --ad ep01 -- python %USERPROFILE%\Kanallar\Engineered\tools\drive.py <film-klasoru> 1 4
   ```
   Kaldığı yerden devam için başlangıç aşamasını ver: `... drive.py <klasor> 3 4`.
3. **Ses kayması** (aşama 1 sonrası anlatım tempo/ton bozuksa): `python %USERPROFILE%\testbench\speed_1106\voicefix.py %USERPROFILE%\CodexOutputs\<film> --apply`, ardından `drive.py <film-klasoru> 1 4`. Yalnız denetimin işaretlediği parçalar yeniden seslendirilir.
4. **Teslim:** render bitince ZIP, `DOCUMENTARY_DELIVERY_ROOT` klasörüne (`%USERPROFILE%\Belgesel_Teslim\teslim`) düşer. `render_result.json`'da QA notlarını oku.
5. Her filmden sonra: ne bozulduysa ve nasıl çözüldüyse `beyin/araclar/ekle.py --tur ders ...` ile yaz. Bir sonraki film ve sonraki oturum bunu otomatik görür.

## 8. Sık sorunlar (önce `ara.py`)
| Belirti | Bak |
|---|---|
| gemweb "tüm hesaplar hata verdi" | Firefox profilinde Gemini oturumu düşmüş olabilir: o profille Gemini'yi aç ve yeniden gir. Ya da 5 saatlik kota bitmiştir: panelde `kredi_5s` |
| Aşama 3'te YouTube indirmesi düşüyor | Firefox varsayılan profilinde YouTube oturumu, PO token sunucusu (:4416), `yt-dlp` sürümü |
| Render çok yavaş / NVENC hatası | `nvidia-smi`, aynı anda başka render var mı. NVENC sınırı gevşetilmez, film sayısı azaltılır |
| RAM düşüyor | eşzamanlı film sayısını azalt (ffmpeg kesim + chrome render RAM yer) |
| Pocket aynı cümleyi tekrar ediyor | cümleyi yeniden yaz (beyinde kayıtlı çözüm) |

## 9. Bu makineye özel ayarlar
Bu makinede değişen her kalıcı ayarı (port, model adı, kritik dışı yapılan kontrol) Claude `%USERPROFILE%\Kanallar\Engineered\CLAUDE.md` sonuna "Bu makine:" başlığıyla yazar. Böylece `git pull` + `kur.py` sonrasında hangi farkın bilinçli olduğu bilinir.
