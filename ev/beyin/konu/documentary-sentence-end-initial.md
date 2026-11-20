---
tur: konu
aciklama: Cümle sonu kuralı baş harfi cümle sonu sayıyordu: 'Jack D. | Gillum' diye adı böldü, Codex incelemesi FAIL verdi.
kaynak: auto-memory C--Users-meteh/memory/documentary-sentence-end-initial.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
`documentary_voice_step2.py` cumle sonunu regex ile buluyordu; tek buyuk harf + nokta (bas harf) cumle sonu sayildi, "engineer Jack D." | "Gillum." diye ad bolundu, Codex `semantic_boundaries: FAIL` verip stage 2'yi kapatti. Duzeltme: `_ends_sentence(word)`: bas harf (tek buyuk harf + nokta) ve yaygin kisaltmalar (Dr., Mr., Inc., vs., No., etc.) cumle sonu degil; `_batches`, `_complete_sentences`, `_refine_semantic_boundaries`'e baglandi. Sonuc: 103 -> 102 sahne, Codex PASS 4/4.
**Ders:** EN/TR'de nokta cumle sonu demek degil; bagimsiz denetci hata bulunca once onun bulgusunu oku, sonra kodu duzelt. Ilgili: [[documentary-three-editorial-rules]], [[documentary-stage3-status-acceptance]].
