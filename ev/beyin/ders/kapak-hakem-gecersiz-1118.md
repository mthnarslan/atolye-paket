---
tur: ders
aciklama: LLM tiklama hakemi (12'li akis izgarasi) gercek basariyi ayiramiyor: cok-tutan rakibi %38 secti (sans %50); bizim YZ kapaklari 250/252 rakibi gecti
kaynak: testbench/kapak_v5
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# kapak-hakem-gecersiz-1118

Ters kontrol 18 Kas: hakem_dogrula.py (bizden kapak yok; 6 cok-tutan + 6 az-tutan rakip, 21 nis x3) -> ilk secim cok-tutan 24/63=%38, gecilenlerde az-tutan %46: sanstan iyi degil. Kafa kafaya (tik_h2h.py, yeni+eski bizim + 10 rakip, 252 istek): 250'de birinci bizim kapaklardan biri, gercek izlenmeleri 0-211 olmasina ragmen -> hakem YZ uretimi parlak gorsele onyargili. Sonuc: 'hakem testini gecti' kanit DEGIL. Kural: her kapak hakemi once gecerlilik kapisindan gecer (bilinen cok/az tutan rakip ciftlerinde sansin belirgin ustu), gecmezse kullanilmaz. Dosyalar testbench/kapak_v5 (dogrula.json, tik_h2h.json).


## Ikili kapi (ayni gun)
hakem_cift.py: ayni nisten cok-tutan vs az-tutan rakip cifti, "hangisi daha cok tiklandi" -> 33/84 = %39 (sans %50). Iki test de ~%38: YZ hakemi ders kitabi kurallarini (kalin yazi, yuksek kontrast, once/sonra bolme, kirmizi ok, isaret eden yuz) oduller; az tutanlar da bunlari yapiyor. olcum2.json (203 kapak): renk/parlaklik/kontrast/yazi/gercek-foto/yuz gruplar arasinda ~ayni; tek fark merak gucu 3.99 vs 3.55. Gercek kanit yalniz YouTube Studio Test & Compare.
