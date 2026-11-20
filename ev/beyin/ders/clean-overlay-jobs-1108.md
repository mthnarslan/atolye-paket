---
tur: ders
aciklama: clean_overlay --jobs toplu mod: modeller bir kez, kutu basina kirpim, ProPainter surec ici; NaN siyah kutu duzeltildi
kaynak: oturum 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# clean-overlay-jobs-1108

VideoLab/clean_overlay.py --jobs jobs.json (cwd VideoLab, venv python). Is: {i,o,boxes,force}. pp_inproc.py ProPainter'i surec ici calistirir; fp16 NaN -> pad/fp32 yeniden dene (siyah kutu sebebi). Ayni yukte eski 4 klip 1168 sn, yeni 300 sn. Ayrinti testbench/gaia_1108/clean_speed.
