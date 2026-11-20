---
tur: konu
aciklama: Aşama 3'ün 500 vermesinin kök nedeni: kabul listesinde status ile review verdict karıştırılmıştı.
kaynak: auto-memory C--Users-meteh/memory/documentary-stage3-status-acceptance.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Asama 3 iki hatayla 500 verdi. (1) `runner.py` unresolved kontrolu `("PASS","ACCEPTABLE")` diyordu; `ACCEPTABLE` bir review verdict, kodun yazdigi status'lar `PASS` ve `PASS_WITH_WARNINGS` -> teslim edilecek kesitler "unresolved" sayildi (satir 2026-10-20'den beri yanlisti, ilk kez 3 shot PASS_WITH_WARNINGS cikinca patladi). (2) Windows okuma/yazma yarisi: `io.py::save()` `os.replace` ile atomik ama `load()`'in retry'si yoktu, 16 ms sonra okuyan shot PermissionError -> `WORK_FAILED` -> 500; `load()` retry'ye girdi, `save()` butcesi 8 -> 40.
**Ders:** listedeki isim o noktada gercekten uretilen degerin adi olmali (verdict != status); yeni kontrol listesinde degerleri grep'le dogrula. Teslim raporu notlu kesitleri adlandirmiyordu; iki teslim yolu artik `runner._delivered_with_note()` kullanir. Ilgili: [[documentary-pipeline-project]].
