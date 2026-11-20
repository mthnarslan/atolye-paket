---
tur: ders
aciklama: GPT 4 şerit doluyken VIDEO incelemesi Flash low+high çiftine: ikisi de geçer derse kabul, yoksa GPT sırası (prod 452d117)
kaynak: testbench/judge_overflow_1107 (rules.py, live_test.py); documentary_materials 452d117
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# gpt-dolu-flash-kabul-1107

İstek boyutu darboğaz değil: GPT inceleme isteği ortanca 79 KB (en büyük 261 KB), boyut~süre korelasyonu 0,11; asıl kayıp GPT kuyruğu (ortanca 37,5 sn bekleme + 22 sn çağrı). Flash'ı tam hakem yapmak (taşma) 31 GPT redinden 3-4'ünü geçiriyor (%10-13; sızıntılar 3D ve CARD). Asimetrik kural: Flash sadece KABUL edebilir; VIDEO'da low+high ikisi de _deliverable_review geçerse kabul, değilse GPT. Replay 156 inceleme + canlı test: VIDEO 0/14 sızıntı (3 bağımsız koşu), GPT'nin kabul ettiği VIDEO'ların ~%60-72'si GPT'ye hiç gitmiyor. Kapatmak: DOCUMENTARY_REVIEW_FLASH_ACCEPT=''. Canlı partide izle: codex_flashaccept_*.json sayısı, aşama 4 QA ret oranı.
