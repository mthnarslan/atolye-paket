---
tur: ders
aciklama: 3D organik konuda %15 geçiyor (katı konuda %54): organik-tek sahnelerde 3D puanı ≤3, prod 5caf8e1
kaynak: testbench/pkg_1107/check_3d_topic.py, replay_make_plan.py; documentary_materials 5caf8e1
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# organik-3d-cap-1107

EP02-05 shot_done GENERATE_3D: sadece organik cümle (sel, buzul, vadi, fırtına, huni...) 6/40=%15, sadece katı (temel, ev, ray, radar, EF ölçeği, mph) 27/50=%54, ikisi 13/43, hiçbiri 23/75. Kural (planning.py _cap_organic_3d, DOCUMENTARY_ORGANIC_3D_CAP=3, 10 = kapalı): katı ipucu olmayan organik sahnede Flash 3D puanı en çok 3; skorlar diskte değişmez, her okumada uygulanır; erken 3D kilidi (>=7) de bu sahneleri almaz. Çevrimdışı make_plan tekrarı (tests/replay_make_plan.py, testbench/pkg_1107): EP03 3D 30->24 (6 organik çekim ANIM/PHOTO/VIDEO/MOTION'a), EP04 aynı, EP02/05 ±1, karışım hedef içinde. Canlı etki sonraki partide ölçülmeli (organik 3D shot_done sayısı).
