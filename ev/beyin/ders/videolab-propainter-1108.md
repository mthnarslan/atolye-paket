---
tur: ders
aciklama: Logo/yazi silmede ProPainter (fp16, kirpik bolge, sahne sahne) acik ara en iyi; 4 GB GPU'da 57 kare 33 sn
kaynak: VideoLab oturumu 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# videolab-propainter-1108

Kurulum: C:/Users/meteh/videolab_ai (venv --system-site-packages, ProPainter + weights). Yontem: yazi bolgesi 64 px payla kirp (8'in kati), sahne kesimine gore bol, maske PNG, inference_propainter.py --fp16 --save_frames --mask_dilation 4, ciktiyi 9px genisletilmis maske+1.5 sigma yumusak kenarla orijinale yapistir, ses -c:a copy. Red Bull opak yazi: kalan kirmizi piksel 14860->0, statik/bulut/agac sahneleri temiz; durgun orman sahnesinde hafif kafes dokusu kaliyor (arka plan hic gorunmuyor). fp32+genis pencere duzeltmedi, 9x yavas; mask_dilation 1 kirmizi kenar birakti. BBC yari saydam logo: ProPainter unblend'den iyi (ayrisma 3.42 vs 3.18, hareket 0.92 vs 0.80, yuzgec kenari keskin, hayalet hp ~0). Lisans: ProPainter NTU S-Lab ticari olmayan. LaMa (Apache) denemesi auto-mode izin engeline takildi. Betikler: oturum scratch pp_prep.py/pp_compose.py.
