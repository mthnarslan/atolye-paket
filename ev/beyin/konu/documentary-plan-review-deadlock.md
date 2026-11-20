---
tur: konu
aciklama: Plan inceleme kilidi: onarım prompt'u kategoriyi sabit tutuyordu, reviewer '3D/diagram' isteyince istek karşılanamıyor ve üretim tümden duruyordu.
kaynak: auto-memory C--Users-meteh/memory/documentary-plan-review-deadlock.md
olusturma: 2026-10-22
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
2026-10-22 soguk kosuda film ikinci kez teslim edilemedi: `planning.py:254` "Plan did not PASS Codex API review after two repairs; production blocked". Kok neden yapisal kilit: `_refine_goals` modele "Categories and timing are fixed" diyordu ve kategori degisimini reddediyordu, oysa reviewer'in en sik istegi "bunu 3D/diagram olarak goster"di (9 itirafin 4'u) -> istek karsilanamaz, 3 turda escalate, FAIL, uretim durdu (3D uretim yolu saglamdi).
Duzeltme: (1) `_apply_review_requests()` fix metninde 3d/diagram/schematic/cutaway gecen shot'lari 3D'ye cevirir (hook ilk 30 sn VIDEO kalir, 4 sn statik taban korunur; karisim tolerans icinde kalan en genis istek kumesi aramayla secilir, istekler grup olarak yanitlanir). (2) `_material_pool(catalog)` reviewer'a havuzu gosterir, havuzda olmayan malzeme plani FAIL ettirmez; payload'a `hard_rules` eklendi. (3) Onarim prompt'u kategoriyi oldugu gibi yazar, yanlis alan duzeltilir, hata firlatilmaz.
**Ders:** denetim dongusu karsilanamaz geri bildirim istiyorsa kapiyi gevsetme, istegi karsilanabilir kil. Ilgili: [[documentary-three-editorial-rules]].
