---
tur: ders
aciklama: Fotograftan neon cizgi (Isaac tarzi): kamuflajda XDoG gurultu; mean-shift x2 + Canny + uzun cizgi + GrabCut maske temiz
kaynak: hf/isaac1 2026-11-13
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# neon-iz-fotograftan-1113

hf/isaac1/tools/neon.py (XDoG+CLAHE): tek nesne (tufek, kask) icin iyi. Kamuflajli asker fotosunda XDoG desen gurultusu verir. tools/neon2.py: pyrMeanShiftFiltering 2 kez -> Canny -> kisa cizgileri at -> istege bagli GrabCut ozne maskesi (rect) + dis hat; cikti turuncu cekirdek+parilti RGBA. Goruntu basi ~1 dk, arka planda kos. Gozluk gibi kucuk karmasik nesnede ikisi de cop; SVG ile ciz. Marker daire/alti cizgiyi dokuman satirina hizalamak icin svg'yi <b> icine koy (position:relative, svg %128 genislik, pathLength=1 + dashoffset tween).
