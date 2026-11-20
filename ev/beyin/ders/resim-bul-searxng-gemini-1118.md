---
tur: ders
aciklama: Gercek arsiv fotosu: Kanallar/resim_bul.py (SearXNG gorsel + stok/filigran ele + Gemini kontak sayfa hakemi) 14 beat ~2 dk, 13 OK
kaynak: Ornek_WA 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# resim-bul-searxng-gemini-1118

Kullanim: python Kanallar/resim_bul.py beats.json --cikti DIR (beat: id, ne, sorgular). SearXNG VDS :8888 (yoksa yerel) -> getty/alamy/imago/akg vb. URL'ler elenir, wikimedia/bundesarchiv/europeana one alinir -> paralel indir (Commons orijinali yerine 1920px thumb), boyut+ahash kopya eleme -> numarali 3x3 kontak sayfa -> gemweb puan 0-10 (modern/cizim/filigran/yazi ceza). Cikti <id>.jpg, <id>_2.jpg, rapor.json; puan<6 ZAYIF. Saarland (Ornek_WA) 14 beatte 13 OK; zayif olan harita cikti, atildi. Secilen fotoyu yine gozle bak: b13 kartpostal yazili cikti, yedek alindi; Lens fotosunda Ingilizce alt yazi vardi, %9 kirpildi. GPT iscisinin test edilmis sorgu kutuphanesi Ornek_WA/isci_sorgu/sorgular.json (beat basi 4 sorgu).
