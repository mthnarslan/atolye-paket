---
tur: ders
aciklama: 6 kanal x 18 video kapak v4: kanal kimligi + video basina rakip referans; Kingmakers net kazanc, guclu kanallarda ±1 gurultu; G-Labs 'right third' bolunmus panel tuzagi
kaynak: testbench/kapak_kanal, ortak-site 5ae0b83
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# kanal-kapak-v4-1118

testbench/kapak_kanal: havuz->ilgi->olc->sec2->uret.py (G-Labs NBP 15 paralel, ref=yayindaki kapak+video referanslari, 'style reference only, do NOT copy text/badges/mascots')->yazi_kanal.py (kanal basina font/renk/rozet, yerel PIL yazi)->puanla->site_kanal.py (kapaklar.json+analiz.json+ZIP). Sonuc (merak, yayindaki->v4): Kingmakers 3->4-5 (portre+konu adi kalibi zayifti, net kazanc); Mara, Router, Naufragios, Lykov iyilesti; Limit Clock, Orca, Weapons Hot, Poon Lim esit/±1 (gurultu, model okumasi ±1 oynar). Limit Clock v4 mobilde 3.0 vs 3.5 hafif kotu. Tuzaklar: (1) istemde 'right third X' / 'left side Y' G-Labs'ta iki panelli sahne uretir, 'no split screen' yetmez; 'one single continuous wide photograph' + bolge adi vermeden yaz. (2) Ikiye bolunmus soru (WHAT GOES / FIRST?) ikinci satiri kucuk kalirsa okunmaz: y2 '?' ile bitiyorsa iki satir ayni boy. (3) Videosu olmayan kanal (Army Loadouts) atlanir. (4) Konu havuzu dar ise (Router 43 aday, 0 guclu) genis havuzdan alinan referanslar konu disi olabilir. site_kapak_wrath/site_ekle2.py index.html'i yeniden yazar, kosma.
