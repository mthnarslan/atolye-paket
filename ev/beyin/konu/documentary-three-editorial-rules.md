---
tur: konu
aciklama: Belgeselin editoryal kurallari ve kapilari: kaynak kotasi 2, konusan kafa yasagi (YuNet, hook 0.08 / film 0.02), hook ses senkronu kapisi, yanik altyazi temizligi
kaynak: auto-memory C--Users-meteh/memory/documentary-three-editorial-rules.md
olusturma: 2026-10-22
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
2026-10-21'de kullanici teslim edilen filmi izledi ve hiz icin bypass edilen kurallari isaretledi; hepsi kod seviyesinde kilitlendi (`C:\Users\meteh\.gemini\scripts\documentary_materials\`). Genel ders: **prompt tavsiyedir, kapi degildir**; olculebilir karsiligi varsa koda tasi.

**1) Kaynak kotasi = taban YouTube id basina en fazla 2 kesit.** `reservations.py::MAX_USES_PER_ORIGIN = 2`; `runner.py::_reserve_sources` sert `raise`. Chunk id'leri (`_000`) ayri kaynak sayilmaz (`origin_id()`). `render_result.json`'a `source_usage` bolumu yazilir; kullanicinin "ayni video 5 kez" iddiasi artefaktlarda tekrarlanamadi (<=2), eksik olan raporlamaydi.

**2) Konusan kafa / roportaj yasagi** (ses adi gecmeyen talking-head yasak; ad/meslek geciyorsa serbest). Tespit YuNet (`forensic_gate_evaluator.py::detect_talking_head`, model `~/.gemini/config/scripts/video_quality_gate/yunet.onnx`), `conf >= 0.70` ve `area_ratio >=` esik: **hook 0.08, film 0.02** (`runner.py::_FILM_FACE_AREA`); ornek sayisi hook'ta 2 kare, filmde 5. Hook'ta uc baglanma noktasi (ana filtre, Flash zaman asimi yedegi, NO_MATCH havuzu) `_native_hd` + `_has_motion` + `not _talking_head_verdict`. Izin: `editorial_gates.py::narration_allows(narration, source_text)` (kaynak kisi adlandirmali **ve** anlatim o kisiyi adlandirmali); kurum/yer sozcuklu buyuk harfli dizi kisi degildir (kelime frekansi listeleri ise yaramadi). Hem seciciye hem nihai materyale (`_film_talking_head`) uygulanir; reddedilen shot fotograf/3B'ye duser. OpenCV yoksa dedektor None olur, kural prompt'ta kalir.
- **Dedektor hatalari (duzeltildi):** (a) `ffmpeg -vsync 0` ffmpeg 9'da kalkti, tek gecis `select` olu, kod yalniz ilk kareye bakiyordu (iki ayri `-ss` seek de daha ucuz); (b) YuNet `cv2.FaceDetectorYN` global ve thread-safe degil, 8 thread'de cagrilarin yarisi assertion ile patlayip `except Exception` ile "yuz yok" sayiliyordu, kapi ters calisiyordu -> `_TALKING_HEAD_DETECTOR_LOCK`; (c) `round(position*25)` 25 fps varsayimi yanlis, seek saniye cinsinden olmali.

**3) Hook ses senkronu:** `runner.py::_hook_line_matches(asset, shot)` hook adayini anlati satirinin anlamli kelimeleri ile adayin kendi metni arasinda kelime kesisimine gore eler (`hook_unmatched_line_filtered`); metni olmayan aday elenmez. Tuzak: `dict.get()` ile `None` -> `"none"` her adayla eslesiyordu, alan adlari sizdi; `_line_words` bos alani atlar. `shot.get("hook_shot")` hic set edilmedigi icin recovery'deki "hook'u once onar" kolu sessizce hic calismiyordu; artik `timeline_start_sec < 30`.

**4) Yanik altyazi temizligi:** `subtitle_gate.py::has_burned_in_subtitle` (mutlak beyaz esik >=225, satir yapisi, **960 px** orneklem, 3 kareden 2'si); `render.py` isaretli kaynakta alt %20'yi kirpip **buyuterek** doldurur. Bilinen kalan: B&W beton fotografi yanlis pozitif; yazi 0.60 yukseklikteyse alt kirpma yetmez.

Ilgili: [[dynamic-rules-not-video-specific]], [[documentary-stage3-status-acceptance]], [[documentary-20min-budget]].
