---
tur: ders
aciklama: gemweb :8790 10 hesap (u0-u4 + p0-p4, kullanicinin TR SOCKS5 proxy'si): 10 paralel 10/10 dogru, 19 sn
kaynak: testbench/gemweb_1116/par10_test.py
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# gemweb-10-hesap-1116

16 Kas: p0-p4 canli eklendi (restart yok). 10 paralel kisa metin istegi: 10/10 dogru, 10 ayri hesap, istek 4-19 sn, toplam 19 sn. Proxy 9router/antigravity degil; kullanicinin kendi listesinden secip FoxyProxy'ye elle girdigi TR SOCKS5, G-Labs ile ortak. Coklu kanal test turunda kanal basi <=4 paralel. Betik testbench/gemweb_1116/par10_test.py
