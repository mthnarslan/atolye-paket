---
tur: ders
aciklama: Büyük indirme (torch pip, HF snapshot) hattı doldurunca gemweb'de makine çapı DNS/proxy hatası; tek tek hesap yakılıyor, istek düşüyordu
kaynak: testbench/gemweb_1116/istek.jsonl, yama_ag_1119.py
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# indirme-hat-dolu-gemweb-ag-1119

11-19 14:20 ve 14:40: paralel torch pip kurulumu + HF snapshot indirmesi interneti doldurdu; aynı anlarda u hesaplarında DNS hatası, p hesaplarında proxy connect timeout (14:10 sonrası 81 ağ hatası; 10 dk kovada 46). Sunucu her hesabı ayrı ayrı 30 sn dinlendiriyor, istek 'tüm hesaplar hata verdi' ile düşüyordu. Çare: (1) gemweb işleri sürerken büyük indirme başlatma, indirmeyi tek tek yap; (2) server.py yama_ag_1119: 30 sn içinde >=3 farklı hesapta ağ hatası = makine çapı kesinti, hesap cezası yok, herkes 10 sn bekleyip yeniden dener (GEMWEB_AG_ESIK). Disk doluluğu (5 GB) da aynı pencerede vardı; low/high testi o ortamda effort farkı göstermedi.
