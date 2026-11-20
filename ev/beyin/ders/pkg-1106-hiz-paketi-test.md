---
tur: ders
aciklama: Hiz paketi (precheck Flash-low, codex 4 lane, review oncelik, glabs 3-slot kilit, searxng bos-sonuc retry, early3d retry) testbench'te 23/23 unit + mini film 4/4 PASS; prod'a gecis APPLY.md
kaynak: testbench/pkg_1106/RESULT.md
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# pkg-1106-hiz-paketi-test

Paket: C:\Users\meteh\testbench\pkg_1106 (patched/, APPLY.md, RESULT.md). Mini film pkg kodunda: precheck 14/14 flash, review 11/11 codex, flash_review 0, codex kuyruk max 7.8 s. Asama 3 634 s vs prod 424 s farki icerik varyansi (plan review FAIL ekstra tur +80 s, reallocation +73 s). Ders: testbench koprusu SCRIPTS yolunu sabit kodluyor (C:\Users\meteh\.gemini\scripts) -> kopyada Path(__file__).parent yap, /diag production_code_signature ile dogrula; aksi halde prod kodla test edersin. Planlama GPT review'i 45 s ReadTimeout ile her kosuda 1 kuyruk olumu veriyor (prod'da da var) -> acik is.
