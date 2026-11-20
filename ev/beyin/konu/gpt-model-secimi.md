---
tur: konu
aciklama: GPT model/effort bench: gpt-6.1-sol medium en dengeli (%100, 14,5 sn) vs prod gpt-6-sol low %85; film denemesi nasil kosulur
kaynak: testbench/gptbench; testbench io.py gptpick 5917338
olusturma: 2026-11-04
guncel: 2026-11-06
yazan: claude
onay: 
etiket: llm,gpt
---
---
tur: konu
aciklama: GPT model/effort bench: gpt-6.1-sol medium en dengeli (%100, 14,5 sn) vs prod gpt-6-sol low %85; film denemesi nasil kosulur
kaynak: testbench/gptbench; testbench io.py gptpick 5917338
olusturma: 2026-11-04
guncel: 2026-11-04
yazan: claude
onay: 
etiket: llm,gpt
---
# gpt-model-secimi

GPT model/effort karsilastirmasi (3-4 Kas 2026, VDS :8765). Bench: `C:\Users\meteh\testbench\gptbench\`, sayfa :8441.

- **En dengeli:** `gpt-6.1-sol` medium: dogruluk %100, medyan 14,5 sn, Turkce 9,3/10.
- **Uretimdeki** `gpt-6-sol` low: dogruluk %85.
- Film uzerinde deneme (DIFF_MINI, taraf basina 2 film) hazir ama kullanici iptal etti (Flash yuku istemedi). Calistirma: `testbench\gptbench\run_side.ps1 A 2` ve `run_side.ps1 B 2 gpt-6.1-sol medium`. Testbench `io.py` dali `gptpick` 5917338 env ile model/effort secer (`DOCUMENTARY_CODEX_MODEL`, `DOCUMENTARY_CODEX_EFFORT`).
- Prod'da istenen ve donen model adi ayni olmali, yoksa istek reddedilir [[documentary-codex-concurrency-and-model-name]].
GPT biterse yedek model: [[gpt-replacement-model]].
