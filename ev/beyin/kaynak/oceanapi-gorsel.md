---
tur: kaynak
aciklama: OceanAPI gpt-image-2.5-flare kapak üretimi: ytmarket_run/bin/ocean_img.py, ~30 sn, 5 kredi; User-Agent şart (yoksa Cloudflare 1010)
kaynak: deneme 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# oceanapi-gorsel

Uç nokta https://api.oceanapi.dev/v1/images/generations (OpenAI uyumlu, cevap data[0].b64_json, 1672x941 PNG). Oran istemin son cümlesinde: 'Set the aspect ratio to 16:9.'; size parametresi yok. Anahtar ytmarket_run/secrets/oceanapi.key (ekrana basma). urllib varsayılan User-Agent'ı Cloudflare 1010 ile reddediliyor; header ekle. Ara sıra 504 veriyor, tekrar dene (başarısız üretim ücretsiz). Başlangıç 100 kredi = 20 görsel. İspanyolca aksanlı kapak yazısını (DÍAS) doğru basıyor. İstemde kişinin kökenini/ifadesini açıkça yaz: yazmayınca Poon Lim Avrupalı çıktı, sonra gülümser çıktı (gerilim kaybı). Poon Lim denemesi: ytmarket_run/thumbs/poonlim (_compare.jpg).
