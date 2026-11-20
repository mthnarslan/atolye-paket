---
tur: konu
aciklama: Part 1 (ses) incelemesi: elle yazilmis sahte PASS (error_type varsa PASS degil), segmentli denetim 62-74 sn, ACCEPTANCE_POLICY segment yolunda, _asr_contradicts, tablo ayraclari TTS'e sizdi
kaynak: auto-memory C--Users-meteh/memory/voice-stage1-audit-findings.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Part 1 (ses, Dify "Belgesel Uretim Hatti" arkasi, kopru :8099 stage 1..4) incelemesi, 2026-10-20/21.

**Sahte PASS dersi:** `voice_audit.json`'daki PASS'i elle yazan bir script uretmisti (`verdict`/`next_step_allowed`/`criteria` elle PASS, `error_type` silindi, hash'ler manifest'ten yeniden yazildi); gercek denetim (`voice_gemini_review.json`) ReadTimeout ile dusmustu, yani ses kalitesi hic dogrulanmamisti ama 2. adim kilidi acti. Kodda otomatik PASS yolu yok, sorun elle dosya yazimiydi. **Guard: `gemini_audio.error_type` varsa hash'ler tutsa bile PASS sayma.**
**Timeout kok nedeni:** `documentary_voice_gemini_review.py` 891 sn'lik sesi tek parca base64 (7,1 MB, boyut sorunu degil, gateway isleme suresi) gonderiyordu: 189,3 sn -> `timeout=(10,180)` ReadTimeout. Cozum: segmentli/paralel denetim (6 segment, `parallel_segments: 6`); 1.4 artik 62-74 sn, PASS.
**Segment yolu duzeltmeleri (canli kosu 277,7 sn FAIL'den ogrenildi; 9 bulgudan yalniz 2'si gercek):** (1) `ACCEPTANCE_POLICY` yalniz `_review_whole` yolundaydi; `_review_segment` prompt'una eklendi. (2) JSON semasinda `warnings` alani yoktu, model harf-harf okuma gozlemini `issues`'a koyup FAIL ediyordu; `SEGMENT_PROMPT`'a `warnings` eklendi (`validate_segment_review`, `_merge_segment_reviews`). (3) Onarim modelin her bulgusunu yeniden sentezliyordu; `documentary_voice_repair.py::_asr_contradicts()` bagimsiz Whisper onaylanan kelimeleri gosterip raporlanani gostermiyorsa bulguyu eler. Sayi normalizasyonu sart ("sixteen hundred" -> "one 600"; `normalized_number_tokens()` ikisini 1600 yapar); karsilastirma kelime dizisi uzerinden ("west" in "midwest" tuzagi).
**Tablo ayraclari TTS'e gidiyordu:** script'in `====` satirlari "== Math go" diye seslendi; `documentary_voice_engine.py` tablo ayrac filtresi `set("|:- `=~_")` oldu.
Ilgili: [[documentary-20min-budget]], [[documentary-pipeline-project]], [[pipeline-v2-deploy-regression]].
