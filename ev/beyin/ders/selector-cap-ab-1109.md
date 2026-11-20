---
tur: ders
aciklama: Selector compact+cap: EP02 240 sn pilot gercek A/B (router): cap 30 -39% prompt token, -29% istek, 53/53 PASS; hiz farki varyans icinde
kaynak: testbench/ab_1109/results/EP_A2,A3,B2,B3.json
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# selector-cap-ab-1109

Ayni tohum katalog (EP_A1), testbench/ab_1109. A2/A3 prod: 286/290 istek, 1,318/1,354M prompt, 696/839 sn, 55/53 PASS. B2 (DOCUMENTARY_SELECT_COMPACT=1, CAP=40, 3D talimati VIDEO'da kirpik, NO_MATCH sonrasi tam liste): 230 istek, 0,950M (-29%), 817 sn, 54/54 PASS. B3 (CAP=30): 205 istek, 0,815M (-39%), 856 sn, 53/53 PASS. Asama 3 suresi A'da 696-839 sn oynadi, B farki varyans icinde. REVIEW_REQUIRED 20-22 -> 23-26 (az aday = biraz fazla onarim). Pilot katalogu 103-144 satir; tam filmde prod istemi ~437 satira buyur, B sabit kalir -> tam film tahmini ~-48-50% (olculmedi). Kalan buyuk kalemler hakem: precheck ~2,1M, flashaccept ~0,9M (onaysiz dokunma).
