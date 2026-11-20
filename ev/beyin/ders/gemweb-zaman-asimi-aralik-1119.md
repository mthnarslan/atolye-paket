---
tur: ders
aciklama: gemweb: zaman aşımını 1095 gibi sayıp aralığı ikiye katlamak tüm hesapları kap 1/aralık 21-68 sn'ye kilitliyordu; düzeltme sonrası 40/40
kaynak: testbench/gemweb_1116/istek.jsonl, /tmp/gwt/gorhigh7.log, gorhigh8.log; C:/Users/meteh/AppData/Local/Temp/gwt/gorhigh9.log
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# gemweb-zaman-asimi-aralik-1119

11-19: 14:00'ten beri 82 TimeoutError (görsel+high, Gemini yükü) GECICI sayılıp aralık x2 (30-90 sn) yaptı; 10 hesabın 9'u kap 1, aralık 21-68 sn. İstemci medyan 75 sn iken sunucunun ok medyanı 16 sn: fark kuyruk. Yama (yama_ag_1119): zaman aşımında aralık büyümez, hesap 10 sn dinlenir; aralık yalnız 1095/1013/1100'de büyür; makine çapı ağ kesintisinde hesap yakılmaz. Ölçüm (40 görsel+high, 15 paralel): disk dolu+hat tıkalı 16-18/20 medyan 160-182 sn; temiz ortam eski kod 40/40 medyan 75 p90 170; yeni kod 40/40 medyan 70 p90 190 sunucu ok medyan 19,6 — kalan darboğaz 1095 (hesap başı min aralık), diğer oturumların yüküyle paylaşılıyor. Yeniden başlatma öğrenilmiş aralığı sıfırlar.

## 2026-11-19 (claude)

EK 15:25: 1095 oranı hesap boşluğuna bağlı (13:00 sonrası): <30 sn %23, 30-60 %14, 60-120 %2 → gerçekten hesap başı hız sınırı. ARALIK_UST 90→15 denendi: 40/40 337 sn (90'da 313), 1095 %29 → kazanç yok, 90'da kaldı. Kalan tavan: 10 hesap × ~60 sn güvenli aralık; daha fazla hız = daha fazla hesap.
