---
tur: ders
aciklama: Stage3 500 restart dongusu -> cagri ici medium merdiveni + ret hafizasi; EP03 5 deneme/9000+ sn takili -> tek deneme 1964 sn
kaynak: testbench/darbogaz_1107
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# darbogaz-paketi-1107

7 Kas: documentary_materials 6649e3d + 65cdfa3, scripts 1fc93b5 + e7d74b5, Kanallar 2951ba6. (1) run_pipeline 500 yerine escalate_unresolved merdiveni (V2: ANIM/MOTION 3D'den once) cagri icinde, 2400 sn butce, DOCUMENTARY_IN_CALL_LOOPS=0 kapatir. EP03 canli: once 5 deneme 9000+ sn ve 2 cozulmemis, sonra tek deneme MATERIALS_READY 1964 sn. (2) Plan incelemesi: eski planlar hic PASS almamisti, sadece plan_review_fallback (PARTIAL) ile yasiyordu; _enforce_plan_hard_rules + _align_goals + _lift_banned_rows incelemeden once; bitmis cekim kilidi. (3) Dar cekim kimligi: sadece istem benzeri literaller + ANIM_OUTPUT_VERSION / THREE_OUTPUT_VERSION; eski anahtar goc ile yeniden damgalanir; EP02-05 545/545 REUSE. _work_shot icine yeni string literal koyma, string'i bolen + ekleme bile tum cekimleri bozar. (4) 3D retlerinin %82'si 'soyut bloklar': uretici 5 sekil biliyordu; terrain/water/cone/sphere/house + gokyuzu ile reddedilen 6 EP03 cekimi 0/6 -> 5/6. (5) G-Labs Max Retries koku hesap basina gunluk gorsel kotasi (429) -> havuz biter; anim_guard devre kesici. (6) Ses: ASR sentezle akisli (VDS, ~60 sn grup), test 200->162 sn. (7) Yerel piksel on filtresi ise yaramadi (0 yanlis eleme sartinda %3 yakalar). NO_MATCH %10 bilgisi yanlis, gercek %67. Ayrinti testbench/darbogaz_1107/*/RESULT.md.
