---
tur: ders
aciklama: gemweb hydrogen low: mp4 video image_url ile gercekten izleniyor; kontak sayfasi grubunda tek sayfa yuzunden toptan 'Sorry I can't help with that image' reddi
kaynak: testbench/gemweb_asker_1116/SONUC.md
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# gemweb-asker-1116

Asker (hf/isaac2) Flash cagrilari :8790 gemini-4-hydrogen low ile test edildi (17 istek). sor.py kurgu kiyasi: data:video/mp4 image_url kabul, 44-48 sn, 21-24 madde, klip zaman damgalari kareden dogrulandi (gercekten izliyor). chpick.py: 6 kontak sayfasi/istek, low 16-23 sn, high 49-57 sn; ayni grup low+high her seferinde 'Sorry I can't help with that image' (200 status, JSON degil) dondu; tek tek gonderince yalniz B15 (Charade metro/telefon sahneleri, gorunur sebep yok) reddedildi. Kural: bu cevabi ret say, grubu sayfa sayfa bol, reddedeni atla. Iki low kosu secimi 13/24 ortak; gozle 16 karenin ~13'u uygun. Kanit testbench/gemweb_asker_1116/kanit.
