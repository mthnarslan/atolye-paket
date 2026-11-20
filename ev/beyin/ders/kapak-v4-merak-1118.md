---
tur: ders
aciklama: Kapak v4: merak odakli tek ozne + celiski sorusu, 5 videonun 4'unde merak referans medyanina ulasti; site_ekle2.py index.html'i bastan yazar
kaynak: testbench/kapak_v4, ortak-site 4932ac9
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# kapak-v4-merak-1118

v4 (testbench/kapak_v4): referans analizi (kapak_puan) bulgusuna gore merak gucu odakli; tek net ozne, sade arka plan, yuz/grafik eki yok, yazi basligin celiskisini soru yapar (WHY ONLY EF4?, NO RAIN?, CAN IT LIFT A TRAIN?). Puan (2 okuma ort.): merak A 5/4.5, B 4/4 (ref medyani 4.5, v3 2-3), C 4/5 (v3 3-4), D 4.5/4.5, L 4.5/4.5; ayni oturumda v3 yeniden okununca eski puanlarla ayni cikti (model tutarli). Tuzak: kapak_wrath/site_ekle2.py index.html'de 'let KP=null'..'function show' arasini bastan yazar -> kaVideo/referans analizi silinir; v4 icin yalniz json guncelleyen kapak_v4/site_v4.py kullanildi. Akis: yap_fikir.py -> uret.py (G-Labs) -> yazi.py -> kapak_puan/biz_v4.py -> analiz_site.py -> site_v4.py -> wrangler deploy.
