---
tur: ders
aciklama: HyperFrames/GSAP: transform attr'li SVG <g>'ye GSAP x/scale verince g kaybolur/kayar; dis <g> sarmalayicisina tween et, scale oncesi svgOrigin'i t=0'da set et
kaynak: hf/asker13/tools/build.py
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# gsap-svg-g-transform-1113

asker13 (Apache vs Ka-52): intro helikopterleri gorunmedi cunku GSAP, transform='translate(..) scale(..)' attr'li <g>'nin transformunu eziyor. Cozum: animasyonu bos bir dis <g>'ye ver. Yay (arc) kamasi yanlis yerde donuyordu: scale/rotate tweeninden once st() ile svgOrigin'i t=0'da set et. Ayrica: klipli sahne klip suresi-offset'ten uzun olamaz; etiket gercek klibe uymali (SPIKE NLOS klibine 'Hellfire' yazilmisti, duzeltildi).
