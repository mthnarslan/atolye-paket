---
tur: ders
aciklama: gemweb: 1095/1013/zaman asimi gecici hata artik hesabi 60 sn dinlendirir (eski 900 sn); istemci koparsa sunucu denemeyi birakir; gemweb.py zaman 400 sn; istek.jsonl istek kaydi
kaynak: testbench/gemweb_1116/server.py, Kanallar/gemweb.py
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# gemweb-gecici-hata-soguma-1119

Sorun 11-19: istemlerin ~%4'u ~95 sn sonra Google 1095 aliyordu, hesaba ozel degil; sunucu bunu kalici hata sayip hesabi 15 dk dinlendiriyordu, 10 hesap birlikte dinlenmeye girip 503 'tum hesaplar dinleniyor' veriyordu. Ustelik istemci (gemweb.py) 200 sn'de vazgecip yeniden istek atarken sunucu eski istegi 600 sn'ye kadar denemeye devam ediyordu (zombi yuk). Cozum: server.py GECICI regex (1095|1013|1100|TimeoutError|ReadTimeout) -> GEMWEB_SOGUMA_GECICI=60 sn; sor() her turda req.is_disconnected() bakar; her istek testbench/gemweb_1116/istek.jsonl'a (hesap, sonuc, sn, gecici) yazilir. gemweb.py zaman=400, 503'te 30*(i+1) sn bekler. Yeniden baslatma sonrasi 10/10 hesap hazir, 12 paralel hydrogen high 12/12 ok (5,8-88 sn). Yedekler server.py.bak-1119, gemweb.py.bak-1119.
