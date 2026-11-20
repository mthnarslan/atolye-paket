---
tur: ders
aciklama: Kanal tazelik kuralında son5/önceki5 oranı ≥14 günlük videolardan hesaplanmalı; 3-10 günlükler izlenme toplamadığı için Helix'i yanlışlıkla eledi
kaynak: ytmarket_run/reports/kanal1120/tazelik_1120.json
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# tazelik-orani-14g-1120

Kural (11-20): son10 (≥3 gün, ≥180 sn) medyanı ≥ max(5k, eski medyanın %20'si) VE son5/önceki5 ≥0,25. v1 oranı son10'dan hesaplayınca Helix 0,035 çıkıp düştü (yeni videolar henüz birikmemiş). v2: oran yalnız ≥14 günlük son 10 videodan; medyan koşulu aynı. Kontroller FREMDFORM/Helix/Mapnificent geçti, Ricos (son10 11,7k < 19,9k) düştü. Site: yeni 3/4, örnek 40/43, ref 25/26. Kod ytmarket_run/reports/kanal1120/tazelik_1120.py, ~136 ytapi birimi. İki dizi dönüşümlü kanalda (Lets Read) oran yapay düşebilir.
