# ENGINEERED kanalı

Ortak sistem `~/Kanallar/SISTEM.md` dosyasında (otomatik yüklenir). Burada sadece bu kanala özel olanlar var.

- **Tür:** tarih/teknoloji/felaket belgeselleri (ör. Mayfield 2021 hortumu), ~10 dk, gerçek görüntü + arşiv + motion grafik.
- **Hat:** belgesel hattı — `C:\Users\meteh\.gemini\scripts\documentary_materials`, köprü :8099 (`documentary_native_bridge.py`). Senaryo materyal klasöründen gelir (tablo biçimli senaryolarda sadece anlatım sütunu okunur, `[...]` yönergeleri atılır).
- **Ses (6 Kas'tan beri):** Pocket + Jeff referansı (`DOCUMENTARY_VOICE_ENGINE=pocket`, `DOCUMENTARY_VOICE_REF=C:\Users\meteh\voices\jeff\ref.wav`), film başı ~5 dk. Chatterbox kullanma (4 GB GPU'da film başı 35-60 dk, sayıları bozuyor). Köprü ayrıca `DOCUMENTARY_REMOTE_ASR=root@100.104.78.117` + `DOCUMENTARY_PINPOINT=0` ile çalışır; ortamı değiştirmeden önce çalışan köprünün env'ini psutil ile oku. Ses sahibinin izni var (kullanıcı, 1 Kas).
- **Ses denetimi `reference_voice_match` FAIL** (bir cümle başka sese kayar): otomatik tamir bunu onarmaz. `python C:\Users\meteh\testbench\speed_1106\voicefix.py CodexOutputs\<film> --apply` (aynı metin, yeni seed), sonra 1. aşamayı yeniden koş. İkinci kez kayarsa kısa cümleyi öncekine bağla (`voice_repair_state.json` overrides text; Pocket çok kısa cümlede kayıyor).
- **Kabul edilen istisnalar:** konuşan kafa olmayan ama "talking head" sanılan çekimler için `delivery_waivers.json`.
- **Teslim:** `C:\Users\meteh\OneDrive\Desktop\Channells\ENGINEERED` (ZIP). Kullanıcı Drive'a yükledikten sonra silinir.
- **Örnek video (V2 "Case File" edit, 5 Kas):** `referans\EP01_WRATH_OF_EARTH_V2.mp4` (9:57, 1080p25) + `referans\EP01_V2_EDIT_NOTLARI.md`. Bizim Mayfield teslim paketinden (134 klip, `master_voiceover.wav`, `EDL.json`) başka makinede (`C:\Users\ejder\...\EDIT_V2`, v2_assets.py/v2_build.py) yeniden editlendi. Yeni bölümler bu stile göre: koyu topo harita zemini, bölüm başına mod (FULL/COLLAGE/PRINT/MONITOR), belge + kırmızı kalem halkası kartları, Flow ile kilitli gravür stili klipler, ölçülü SFX. Yayın adı muhtemelen "WRATH OF EARTH" (kullanıcıya teyit ettir).
- **16 Kas'tan beri:** `sf.py` (174/253/337) ve `casefile/cf_common.py:208` Flash'ı `ag/gemini-3.8-flash-low` sabitiyle 9router'dan çağırır, o şu an 503. gemweb hydrogen low testte geçti (`beyin/ders/gemweb-engineered-flash-1116`); prod'a geçiş onay + A/B ister. fullrun/drive koşusu ve izlemesi `operator` alt ajanında, bekleme `bekci.py` ile (bash değil, python'a sar).
- **Hat hafızası:** ortak beyin `C:\Users\meteh\beyin` (oturum başında hook özet basar; belgesel sayfaları `konu/documentary-*`). Film başlatmadan önce ilgili sayfaya bak.

## Toplu film (6 Kas'tan beri, V3 Case File teslimi)
- Girdi klasörlerini tek bir üst klasöre koy (junction da olur: `mklink /J`), sonra arka planda `python tools\fullrun.py <üst klasör> <etiket>`: film başına drive 1-3 → aşama 4 ile paralel `sf plan/prep/build` → `sf render` → `sf mix` → `v3_package.py`. Zaman çizelgesi `Belgesel_Teslim\fullrun_<etiket>\timeline.jsonl`.
- Ses/render/mix yuvaları `Belgesel_Teslim\_slots\*.lock` ile TÜM oturumlar arasında ortak (iki sohbet aynı anda koşabilir, sırayla girerler). RAM 2 GB altına inince yeni adım bekler. Bir sohbette en fazla 5 film.
- Çıkış 1 (aşama 1 FAIL) yeniden denenmez: `voice_audit.json`'a bak (yukarıdaki voicefix), aynı üst klasörle fullrun'ı yeniden başlat (bitmiş işler yeniden kullanılır).

## Film nasıl başlatılır (Mayfield böyle yapıldı, 2026-10-28)
- **Girdi:** Drive'dan inen klasör (ör. `Downloads\Compressed\...\NEW_CHANNEL_EP01_Western_Kentucky_2021`): `04_SCRIPT_EN.md` (numaralı tablo, sadece anlatım hücresi), referans ses `*.wav`, `*_PRODUCTION_KIT.txt`, referans görsel.
- **Önce:** `python C:\Users\meteh\Kanallar\preflight.py`; köprü kapalıysa `C:\Users\meteh\.gemini\scripts` içinde `python documentary_native_bridge.py` (gizli arka plan, log `documentary_native_bridge.log`).
- **Başlat:** `PYTHONIOENCODING=utf-8 python C:\Users\meteh\Kanallar\Engineered\tools\drive.py "<girdi klasörü>" 1 4 > <log> 2>&1` (arka planda). Her aşama için `POST :8099/run {"stage":N,"folder_path":...}`; ilk hatada durur (1 SUCCESS/PASS, 2 PASS, 3 MATERIALS_READY, 4 PASS/PASS_WITH_NOTES). Materyal takılırsa `drive.py "<klasör>" 3 4` ile en fazla 3 kez yeniden.
- **İzle:** drive log, `CodexOutputs\<film>\03_materials\events.jsonl`, `shots\*\result.json`, `voice_progress.json`. Bekçi: `tools\supervisor.py` (döngü / 12 dk olaysız / RAM<1 GB'de çıkar, Claude'u uyandırır) — her uyanışta yeniden kur.
- **Çıktı/teslim:** `C:\Users\meteh\CodexOutputs\<film>\`; 4. aşama ZIP'i kendisi kurar → `Channells\ENGINEERED\<film>\<FILM>_DELIVERY_PACKAGE.zip` + `_DELIVERY_PACKAGE_QA.md`. Drive'a yüklenince sil.
- Mayfield'da 70 ve 97 numaralı çekimler `delivery_waivers.json` ile elle kabul edildi ("3D planlı, ANIM teslim").
- `tools\batch_films.py` toplu vahşi yaşam filmleri içindi (yolları o işe sabit), ENGINEERED için `drive.py` kullan.
