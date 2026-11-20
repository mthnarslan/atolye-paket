---
tur: konu
aciklama: Codex eş zamanlılığı 4→12 (ölçülmüş matris) ve üretimdeki model adı ile kalibrasyon model adının farkı.
kaynak: auto-memory C--Users-meteh/memory/documentary-codex-concurrency-and-model-name.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
**Codex eszamanliligi 4 -> 12** (`system_speed_profile.json`, `codex` blogu): 12'de 23,1 sn / 12 cagri, hiz siniri yok; 16'da 4x HTTP 429 -> 12, 429'suz son seviye. `hedge_enabled: false` (hedge fiziksel istek sayisini ikiye katlar).
**Model adi uyusmazligi (bilincli):** olcum `gpt-6.1-sol` ile yapildi, uretim `gpt-6-sol` cagirir; VDS ikisini de sunar. `io.py` cevaptaki model adinin istenenle eslesmesini zorunlu kildigi icin uretim adi `gpt-6-sol` kalir.
**How to apply:** eszamanliligi degistirirken 429 yoklugunu dogrula; model adi degisirse `io.py` eslesme kontrolunu de guncelle. Ilgili: [[gpt-model-secimi]], [[documentary-pipeline-project]].
