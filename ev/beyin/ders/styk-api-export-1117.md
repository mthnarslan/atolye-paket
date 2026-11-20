---
tur: ders
aciklama: StykAnimate: window.styk API ile poz/animasyon yazma; uygulama ici tarayicida export dosyasi disari cikmiyor
kaynak: Avenox oturumu 2026-11-17
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: 
---
# styk-api-export-1117

Styk (app.stykanimate.com) dokumani v5: styk.editor.serialize()/load(doc). Animasyon _styk.frameSources[frameId] (root_x, root_y=kalca, scale, angles=10 mutlak dunya acisi: govde,bas,kol A ust/on,kol B ust/on,bacak C ust/alt,bacak D ust/alt; 0=sag, +pi/2=asagi) + layerSheet.tracks['layer-1'].keys [{id,tick,interpolation:'linear',value:{frameId}}]. Load hatasi 'Frame source identities must be valid and unique': legacy keyframes'i frameSources ile cogaltma, tek keyframe birak. Export Ctrl+Shift+E; PNG dizisi showSaveFilePicker ile yaziliyor: Claude uygulama ici tarayicida indirme diske dusmuyor ve sayfadan localhost'a fetch engelli. Cozum: ayni poz verisini Python/cv2 ile cizmek (Avenox_inceleme/araclar/karma.py, 450 kare 1080p ~21 sn) ya da kullanici export'u kendi tarayicisinda yapar. setBackgroundColor 'finite numbers' hatasi verdi; arka plan transparent export'ta onemsiz.
