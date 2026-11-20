---
tur: ders
aciklama: Flash pinpoint: 9router YouTube URL'sini izletemiyor; sources.py'de artik varsayilan kapali (DOCUMENTARY_PINPOINT=0), storyboard yedegi calisir
kaynak: fullrun_1106 oturumu; documentary_materials/sources.py:2012
olusturma: 2026-11-06
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# pinpoint-youtube-9router-1106

Test 6 Kas (testbench/speed_1106/pinpoint repro2.py native.py stamps.py, video _ZIfeU3RwYI 7:28 animasyon). 9router: image_url -> 400 'Unsupported mime type image/* in file_data'; video_url 200 89 sn 'Football Manager skin' uydurma; input_video 200 'kagidin tarihi' uydurma; file/file_data/file_id/url 200 'video verilmedi'. Yani 9router uzerinden pinpoint OLUMSUZ, EP05'te 23/23 basarisiz, hep storyboard yedegi calisti (kalite storyboard kadar). Google yerel generateContent + fileData{fileUri: youtube, mimeType video/*} + mediaResolution LOW: gemini-3.5-flash-lite 200 6-8 sn 41k token, konu/stil dogru AMA zaman damgalari yanlis (7:28 videoda 452 sn, UNCONFIRMED karesi 4:50'de, model 452 dedi) -> kullanilmaz. gemini-3.8-flash yerel: 503 high demand (6 Kas ogleden sonra). gemini-3.6-flash: 23 anahtarin gunluk kotasi bitmis. Kalici cozum adayi: io.py'de urls olan cagriyi yerel generateContent'e (3.8-flash) yollamak; .gemini duzenlemesi kullanici izni ister. O olana kadar DOCUMENTARY_PINPOINT=0 bosa 23 cagriyi keser (kazanc birkac sn).

## 2026-11-08 (claude)

11-08: kod varsayilani kapali (sources.py PINPOINT = env DOCUMENTARY_PINPOINT '0'). Acik is kapatildi. Yeniden acmak icin yerel generateContent fileData yolu gerekir (yukaridaki not).
