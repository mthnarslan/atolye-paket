---
tur: ders
aciklama: Ses kütüphanesi: LibriVox/MLS insan sesleri lv_ kartı (build_lv.py), kötü tur_ (vokal DF>=0.01) dil 15 temiz sesi geçince yedek_ses/'e taşınır
kaynak: oturum 4c442fa9 11-20
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: ortak
---
# site-ses-librivox-1120

ortak-site/tools/build_lv.py build_tur.py sonunda çalışır: LIBRIVOX.json TUT -> lv_<dil>_<konusmaci> kartları (dil='Sesli kitap', orj yok -> index.html Temiz/Orijinal düğmesi gizli). Kötü tur_ = df_site.json ortalaması >=0.01; dilde temiz (iyi tur_+lv_) >=15 ise kötüler yedek_ses/'e taşınır, değilse kalır. 11-20: de 19, en 31 temiz -> 28 kötü kart çıktı; es 12, fr 3, pt 5 bekliyor. LibriVox 64 kbps mp3 DF'de çok eleniyor (opus kopya denemesi sürüyor). Deploy: npx wrangler pages deploy public --project-name ortak-atolye --branch main.
