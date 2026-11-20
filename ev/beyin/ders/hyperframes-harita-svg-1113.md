---
tur: ders
aciklama: HyperFrames'te karanlık harita: Natural Earth 10m -> tek global <defs> path + sahne başına <use>; ok marker'ları da global defs'te olmalı
kaynak: hf/asker11/tools/mapgen.py, build.py
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# hyperframes-harita-svg-1113

asker11 (Suwałki): tools/mapgen.py NE 10m geojson'dan ülke path'leri (eşdikdörtgen, cos56, 0.02 derece seyreltme) üretir; 26 ülke ~650 KB. Her harita sahnesinde kopyalamak yerine tek gizli <svg><defs> içinde path, sahnede <use href=#P..> class ile renk -> HTML 705 KB. Zoom: svg'ye GSAP x,y,scale (transformOrigin 0 0), view=(960-cx*s, 540-cy*s, s); etiket/ok ekran koordinatı Python'da hesaplanır. Tuzaklar: (1) sahne başına aynı id'li <marker> tanımı -> url(#ah) ilk (gizli) sahnedekine gider, sonraki sahnelerde ok başı çıkmaz; marker'ları global defs'e koy. (2) League Gothic'te Ł yok, fallback font çirkin -> Bahnschrift condensed (font-stretch 75%). (3) scale'li <g> içindeki gsap x ölçekle çarpılır. (4) 'kal' ülkesi: RUS çokgeninden merkez lon 19-23.5/lat 54-56 olanı KAL.
