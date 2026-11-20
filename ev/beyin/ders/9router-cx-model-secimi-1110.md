---
tur: ders
aciklama: 9router cx/* GPT capraz test: gorev isci icin cx/gpt-6.1-sol, reasoning_effort none (72/72 dogru, ~2.7 sn)
kaynak: testbench/cx_secim_1110
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# 9router-cx-model-secimi-1110

Test: testbench/cx_secim_1110/cxtest.py (8 gercekci tekil gorev: json cikarma, baslik suzme, yeniden yazim, kod duzeltme, Turkce ozet, 4 sn bolme hesabi, VIDEO/PHOTO/ANIM, 300 satir log igne) x3 tekrar. low: 6.1-sol 100% (48/48), 6-astra 100% ama 3.4 sn ve effort none'da HATA verir, 6.1-terra 98%, 5.6-terra 96%, 5.6-sol 92%, 6-sol 85-88%, 6-luna 83%, 5.6-luna 75%, gpt-reserve 71%, daybreak-blue-latest calismiyor (choices yok). none: 6.1-sol 100% (24/24), 6.1-terra 92%. Karar: tekil isler icin cx/gpt-6.1-sol + reasoning_effort none (en az limit). Not: 9router her cx cagrisina ~2.5k prompt token ekliyor; limit asil buradan gider, cok kucuk isleri tek cagrida toplamak tasarruf. Panel girisi gerektigi icin gercek limit dususu olculmedi.
