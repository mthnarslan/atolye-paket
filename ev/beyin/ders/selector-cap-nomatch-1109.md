---
tur: ders
aciklama: Selector aday listesi kirpilinca (cap 40) birlesik uzun cekimde 3x NO_MATCH -> SELECTOR_NO_MATCH_FALLBACK_FAILED; onarimda onceki cevap NO_MATCH ise listeyi kirpma
kaynak: testbench/ab_1109 results/EP_B1.json
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# selector-cap-nomatch-1109

EP02 240 sn pilot B1: cap 40 + compact ile router prompt A2'ye gore -19%, ama merge turunda 16,32 sn birlesik cekim 41 (1968 rekor basinc cumlesi) kirpik listede 3 kez NO_MATCH dedi; A2 ayni cumleyi gevsek BBC Antarktika manzarasiyla (listede 40'in disinda) cozmustu. Cozum (ab_1109/B runner.py): attempt>0 ise en son selector cevabi (flash.json / repair_k/flash.json, olmayan atlanir) NO_MATCH ise cap uygulanmaz. Ders: token icin aday kirpan her degisiklik, merge/onarim yolunda tam listeye geri donmeli; tek PASS-eksigi tum asamayi FAIL yapar.
