---
tur: ders
aciklama: Captcha mantigi kapaklar + akis ayrismasi; v7 kalip 0.93 (rakiplere benzer), v8 1.23; ikinci tur bos renk 6'nin 4'unu one gecirdi
kaynak: oturum 2026-11-19; oturum 2026-11-19
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# kapak-captcha-akis-1119

testbench/kapak_fikir: fikir.py (gemweb high, video basi 4 tur fikir) -> uret.py (2 aday: gercek kaynak + YZ/grafik; G-Labs; yazi kontrast duzeltmesi; elle.json yazi override) -> akis.py (5 rakip+yayindaki+2 yeni 360px tablo; ayrisma = rakiplere ort LAB uzakligi / rakiplerin kendi arasi). 60/60 uretildi (unsafe 400 tekrar denemede gecti). Kaynak dagilimi ai18 kare18 commons12 grafik12; zemin 52 acik 8 koyu. Geride: D_mayfield K2_templar LC2_sleep WH1_gatling WH2_flares O3_ada (rakip seti zaten karisik/acik). Ayrisma tiklama tahmini DEGIL, yalniz goze farklilik. Tuzak: uret.py arguman verince secilen.json'u ezmesin (duzeltildi). Site ortak-site 578094a+.

## 2026-11-19 (claude)

Tum surumler ayrisma medyani: Yayindaki 1.17, v4 1.33 (15 video), v6 0.95, v7 0.93, v8 1.23. v7 bilerek hit rakiplerin dilini taklit ettiginden rakiplere benzer (kotu degil, guvenli). Ikinci tur: rakiplere mock (duz renk+nesne) ile en uzak zemin rengi secilip fikir.py'ye FIKIR_DIR=fikir2 + zemin_hedef.json ile verildi, uret.py OFS=2: Mayfield 1.21, Sleep 1.34, Gatling 1.11, Ada 2.28; Templar 0.95, Flares 0.98 geride (rakipler renk haritasinin her yerinde). Tuzak: koyu zeminde AI kendi yazisini da yaziyor -> cift yazi (Flares 3/4); istemde 'no text' yetmiyor, yazili adayi ele. Site 033140b: yalniz Yayindaki+v7+v8.
