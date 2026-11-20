---
tur: ders
aciklama: Belgesel stage 3 precheck on gemweb hydrogen low: 19/20 matches old Flash; review 12/20 vs GPT, keep it on GPT
kaynak: testbench/gemweb_belgesel_1116/kanit
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# gemweb-belgesel-hakem-1116

testbench/gemweb_belgesel_1116 (build.py rebuilds prompts from receipts, replay.py 40 requests 2 parallel PNG). Precheck exact prompt: 19/20 agreement, false-pass 1/8, false-reject 0/12, 8.9 s median. Review (approximate prompt, GPT truth): 12/20, false-pass 2/6, false-reject 6/14, runs consistent 10/10. Review stays on GPT. Prompts are not stored in receipts: precheck is rebuilt by calling runner._flash_precheck with a fake api, review with runner._review_prompt_code() + eval.
