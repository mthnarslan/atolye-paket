---
tur: ders
aciklama: Kose/kenar logosu: GPU inpaint yerine en-boy korunan kirp+zoom (<=1.2) aninda ve izsiz; EP04 133 isin 129'u
kaynak: GaiaTrace 2026-11-09
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# kirp-zoom-logo-1109

gaia_finish.py crop_out(): logo kutularini kadraj disina iten en kucuk zoom'lu kirpim (pad 12), ffmpeg crop+lanczos 1920x1080. GAIA_CROP_MAX_ZOOM (vars. 1.2). GPU clean_overlay ~1 dk/klip (133 klip 2+ saat, 4 film GPU kilidinde sirada) -> kirpma saniyeler. Kalan (zoom>1.2) GPU'ya. Ayrica: finish loglari dosyaya yonlendirince blok tamponlu/sessiz gorunur ve cp1254 stdout Unicode etiket print'inde COKER -> PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 ile calistir. Cozulmeyen asama-3 cekimleri (final render bloklu) icin drive.py'yi beklemek yerine gaia_finish dogrudan calisir: PASS olmayan cekimler bosluk sayilir, komsu dolgu (<=6 sn) kapatir.
