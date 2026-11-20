---
tur: ders
aciklama: Stage 3 'Plan violated opening hook rule': kisa non-hook cekimde bos kategori (aecc84a) ve kisa filmde hook > VIDEO tavani (507cf71) — ikisi de kodda duzeltildi
kaynak: EP03 batch 2026-11-05
olusturma: 2026-11-05
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# stage3-hook-rule-short-shot-no-category

Belirti: Stage 3 'Plan violated opening hook rule'. Cogu zaman hook sorunu degil, iki kok sebepten biri (ikisi de kodda duzeltildi):
1. Hook disinda <3 sn (75 kare alti) bir cekimin sahnesi VIDEO'yu yasakliyor; PHOTO/3D MIN_STATIC_SHOT_FRAMES ile, MOTION/ANIM `_fits` ile kapali -> satir toplami 1 olamaz -> MILP infeasible -> `automatic_mix_replan_fallback` hook VIDEO sinirini dusurur -> raise. Retry deterministik (scene_scores.json onbellekte). Duzeltme aecc84a: kategorisi bosalan <3 sn non-hook cekime tek satirlik yasak kaldirma.
2. Kisa filmde 30 sn hook filmin %67'si olunca VIDEO tavani (%48) hook kuraliyla celisir (eski kodda da vardi). Duzeltme 507cf71: hook kareleri tavani asarsa tavan hook'a cekilir (event hook_forces_video_share); 10 dk filmlerde tetiklenmez.
Elle kurtarma (eski kod): 03_materials/planning/scene_scores.json'da o sahnelerde 'VIDEO'yu forbidden'dan cikar, VIDEO skorunu >=2 yap, drive.py yeniden.
