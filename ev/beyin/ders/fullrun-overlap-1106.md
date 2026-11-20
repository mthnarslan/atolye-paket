---
tur: ders
aciklama: fullrun: ses tek tek (Chatterbox seri), 4. asama V3 sf plan/prep/build ile paralel; QA paketi yine kapilar
kaynak: ENGINEERED fullrun 1106
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# fullrun-overlap-1106

2026-11-06: Chatterbox chatterbox_serve.py LOCK ile istekleri sirayla isler; 4 film birlikte ses isteyince hepsi sonda biter, GPT/Flash/indirme bosta kalir. fullrun.py artik stage 1'i VOICE semaforuyla film film kosar (drive.py <f> 1 1), biten film hemen 2-3'e gecer. V3 (sf.py) sadece 03_materials (material_plan + shots/*/result.json) ve sesi okur, 4. asama ciktisini (complete_video, QA) okumaz; 4. asama sf plan/prep/build ile ayni anda kosar, QA basarisizsa paket yok, 4. asama cekim degistirirse (result.json mtime) sf plan/prep/build yeniden. --attach: onceki fullrun'in biraktigi drive.py'lari logdan izler (ana sureci olduren drive'lar olmez). Eski scenefile/work/<film> klasoru kalirsa sf plan eski plan_raw.json'u kullanir: tam testten once kenara al.
