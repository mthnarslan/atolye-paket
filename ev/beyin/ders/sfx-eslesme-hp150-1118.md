---
tur: ders
aciklama: sfx_qa dalga eslesmesi: 500 Hz HP gercek whoosh'lari dusurdu, 150 Hz HP (impact ham) gercekleri >=.61, sahteleri <=.39 ayiriyor; konusma altinda pop icin bosluk arama + mikser oz-denetimi
kaynak: Kanallar/sfx_qa.py, Grenzakten_uretim/gz_mix.py
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# sfx-eslesme-hp150-1118

Kesim taramasi: Grenzakten vakalari .96-.99, testbench gercek whoosh >=.61, sahte <=.39 (150 Hz). Esikler degismedi (pop .7, impact .5, whoosh .45, click .5). Konusmaya gomulen pop: gz_build gap() t-.6..t+.3 arasinda 200 ms en sessiz pencere (uzaklik cezasi), gz_mix ayni olcumle .75 alti popu mix'ten cikarip sfx.json'dan siler; 01-03 yerel QA temiz.
