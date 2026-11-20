---
tur: ders
aciklama: LIMIT CLOCK render: capture %62, NVENC encode %13; w3->w5 yalniz %9; Oracle A1 ~2,4x yavas (58 dk/bolum), ek serit olarak yararli
kaynak: testbench/lc_1110/HIZ_ARASTIRMA/RAPOR.md
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# render-darbogaz-1111

20 sn ornek yerel -w3 64 sn (capture 40, encode 8,3 sirali, sabit ~13); A1 4 OCPU -w4 147 sn (capture 54,6, encode libx264 70, extract 14,4) = 7,35 sn/sn -> 8 dk film ~58 dk (yerel tek 14, 2 paralel 21). Aktarim 8,4 MB/s yukleme, 11,5 MB/s indirme (80 MB olcum; eski 0,5 MB/s notu eskidi). Dedup video enjeksiyonu varken kapali, env ile acilmaz. Iki render w3+w3 ~7,3 GiB; finish.py w5 yarisi riski. Hukum: A1 yalniz ek serit (kuyruk >=4 bolum), tek bolum yerelde.
