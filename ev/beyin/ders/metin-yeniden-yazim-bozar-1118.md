---
tur: ders
aciklama: Gecmis (hakemden ~22 alan) metni kuralsiz istemle yeniden duzenlemek her dilde 75-95'e cikariyor; akis kolu da tersi liste kolu da ayni
kaynak: testbench/metin_kural_1118/dil_test/kanit3/abl/akis.log, eslesme_norm.log
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# metin-yeniden-yazim-bozar-1118

Deney 11-18 (testbench/metin_kural_1118/dil_test/akis.py, 10 metin x 2 kol x 6 hakem): secilmis metin (A/S) medyan ~22; ayni olgularla 'tek ip, duzensiz paragraf, kalip kopru yok' F kolu 75-94, ZIT 'her paragraf 2 cumle, liste' L kolu 78-96. Ikisi de bozuk -> bozan yapi degil, yasak listesi olmadan yeniden yazmak. Kural: gecmis metne sonradan serbest LLM duzeltmesi yapma; ya v3 kurallarinin tamamini istemde tut ya da yalniz SIL (mekanik cumle silme, sil.py) uygula. Ek: eslesme (insan vs bizim, 'hangisi YZ') noktalama esitlenince de 57/60 yakaliyor; ama insan parcalari Kurzgesagt ceviri altyazisi, hakem videoyu taniyor ve konu farkli -> adil taban icin ayni konuda, 2022 oncesi, ana dilde insan anlatimi gerekir (insan_konu.py).
