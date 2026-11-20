---
tur: ders
aciklama: Styk PNG export 'Transparent' acik olsa da beyaz zemin verir: styk.editor.setSceneColor(0) (ARGB alfa 0) sart; topluluk varligi headless: library.setSource('public')+loadPublic, importFile(...).document
kaynak: Avenox v3 11-18 olcum
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# styk-seffaf-ve-kutuphane-1118

Styk (app.stykanimate.com) headless export: Transparent dugmesi acik olsa da sahne rengi opak beyaz (ARGB) oldugu icin PNG'ler alfa 255 beyaz cikar. Belgeyi load ettikten sonra await styk.editor.setSceneColor(0) -> gercek seffaf PNG. Taze belgede _styk.frameSources yok: kare sablonu base.keyframes[0]. Topluluk figuru: styk.workspace.activate('library'); await styk.library.setSource('public'); loadPublic(); publicState==='ready' bekle; it=library.itemFor(id); r=await library.importer.importFile(await library.readAsset(it)); r.document.figure_types[0]. Kod: Kanallar/Avenox_inceleme/araclar/styk_sahne.js + styk_cek.py --veri.
