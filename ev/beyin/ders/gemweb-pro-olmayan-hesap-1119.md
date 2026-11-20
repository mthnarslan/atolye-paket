---
tur: ders
aciklama: gemweb'e PRO olmayan (ucretsiz) hesap eklenince isteklerin ~yarisi 400 'bilinmeyen model' aliyordu; sunucu artik modeli tasimayan hesaba gitmiyor. Ucretsiz hesap ekleme (600 kredi, yalniz 'otomatik').
kaynak: testbench/gemweb_1116/server.py, hesaplar/q*.json
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# gemweb-pro-olmayan-hesap-1119

11-19: Profile 2 (proxy 4) ile 5 hesap eklendi; ejderha0758 ucretsiz cikti (kredi_5s 600, modeller yalniz gemini-otomatik). hydrogen istegi o hesaba dusunce gemini_webapi 'Unknown model' ValueError -> BilinmeyenModel -> istemciye 400 (10 istekte 5). Yama (yedek server.py.bak-1119model): _sor_ic basinda modeli tasimayan hesaplar denenen'e eklenir; Unknown model gelirse baska hesap tasiyorsa orada dener. Ardindan 10/10 (1 Gemini reddi). Ucretsiz hesap hesaplar/kapali/'ya tasindi; sunucu 14 hesap. Yeni hesap ekleme: Firefox profili + FoxyProxy, hesap_bul mantigini PROXY ILE kos (ev IP'si sizmasin), dosya {firefox,u,eposta,proxy socks5h}.
