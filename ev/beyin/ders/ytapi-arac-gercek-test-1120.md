---
tur: ders
aciklama: chan_score.py ve niche_hunt.py ytapi.api'ye taşındı ama gerçek çağrıyla denenmedi; bir sonraki gerçek kullanımda who kaydı ve hata kontrol edilecek
kaynak: ytmarket_run/bin, Kanal Bulucu 11-20
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# ytapi-arac-gercek-test-1120

11-20: 11 araç ytapi.api(who=...)'ya taşındı (.bak-1120ytapi). Gerçek çağrı testi: chan_videos OK (2 birim), check_pass ytapi kısmı OK (sonrası test girdisi eksikliğinden KeyError). chan_score (15k kanallık havuz, küçük girdi yok) ve niche_hunt (yalnız search=100 birim) sadece py_compile. İlk gerçek koşuda: secrets/ytapi_usage.json who alanında dosya adı görünüyor mu ve kota hatası RuntimeError olarak yükseliyor mu bak.
