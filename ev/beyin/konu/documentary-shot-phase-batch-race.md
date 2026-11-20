---
tur: konu
aciklama: 3d shot fazinda 121 sn bekleme: _ShotSelectionBatch yarisi (gec gelen shot'un future'i cozulmuyordu), timeout kapsami, adaylarin dusurulmesi
kaynak: auto-memory C--Users-meteh/memory/documentary-shot-phase-batch-race.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
3d shot fazinda 121 sn medyan beklemenin (worker_started -> ilk API istegi) kok nedeni `runner.py::_ShotSelectionBatch` yarisiydi: batch bir kez dispatch edilince `dispatched=True` kaliyor, sonra gelen shot `pending`'e giriyor ama future'i hic cozulmuyordu -> shot `select()` timeout'unu (75 sn) yakip ayni anda solo cagriyi da baslatiyordu. Ek hatalar: `items[:max_batch]` kesiminde disarida kalanlarin future'lari cozulmuyordu (`_resolve_solo`), `select()` timeout'u batch cagrisini kapsamiyordu (tavan `wait + BATCH_TIMEOUT + 15 sn`), `_compact_batch_evidence` 118 adaydan 106'sini dusuruyordu (artik hepsi korunur, aciklama 90 karakter). Duzeltme: `_arrive` dispatch edilmisse `pending`'e almaz, `select()` orphaned ise dogrudan solo secer.
**Ders:** batch/ayar degisikliginde once "future'i kim cozuyor?" diye sor; cozum yoksa o shot timeout'u yakar. Olcum: `tmp/verify_batch_race.py`. Ilgili: [[documentary-20min-budget]].
