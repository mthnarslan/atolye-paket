---
tur: ders
aciklama: Noch harmlos 1_test V1 hakemde %35 YZ (12/34); ham YZ pozitif kontrol %100 (34/34) -> hakem ayirt ediyor, V1 insandan ayirt edilemiyor
kaynak: testbench/metin_kural_1118/dil_test/rapor_de_V1_hydrogen.json; testbench/metin_kural_1118/dil_test/deki/POZITIF_KONTROL.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# nh-tur6-1test-1119

tur6nh (turnuva6.py, korpus kanit3/insan_senaryolu_deki_de, 17 insan, 136 istek): hakem bizim metni 34 ciftin 12'sinde YZ secti (%35,3, Wilson 21-52, bootstrap 15-56). Insan-insan kontrolunde kisi basi YZ orani ortanca 58, aralik 0-92, cift sira tutarliligi 40/50. Sonuc: hakem metni insandan ayiramiyor (<=%50). Eksik: yz_ham pozitif kontrolu bu kosuda yok; hakem regresyon alarmi, guvenlik kaniti degil.

## 2026-11-19 (claude)

Pozitif kontrol (11-19 22:10): gemweb hydrogen low ham metin NH_1test_YZHAM, ayni korpus/hakem, 34/34 YZ secildi (Wilson 90-100). Uyari: ham metinde basliklar/kalin/zaman damgasi bicim izi vardi, temizlenmis ham YZ ile kosulmadi. V1 12/34 (%35, Wilson 21-52), insan-insan ortanca %58.
