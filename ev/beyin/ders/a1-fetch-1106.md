---
tur: ders
aciklama: a1 proxy indirme ev hattindan yavas
kaynak: testbench/speed_1106/FETCH.md
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# a1-fetch-1106

9 EP02 kaynagi (652 MB, 1080p avc1 tam dosya): a1_fetch (8 proxy + scp geri) 158 sn = 4,1 MB/s; yerel ardisik 79 sn = 8,3 MB/s; yerel 4 paralel 29 sn = 22,5 MB/s. Proxy basina ~1,4 MB/s, 208 MB'lik dosya 145 sn. Oneri: kaynaklari a1'e kaydirma; ev hatti daha hizli, a1_fetch (Engineered/tools) sadece ev IP/cerez engellenirse yedek. Yerelde yt_gate concurrency 3->4 denenebilir.
