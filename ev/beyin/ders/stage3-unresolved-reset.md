---
tur: ders
aciklama: Stage 3 'N unresolved shots': attempt>=2 eski sonucu dondurur; result.json + repair_1/2 klasorlerinin ucunu kenara al (rejected.json kalsin) -> taze deneme; empty_sentences.json notu
kaynak: Engineered batch 1105
olusturma: 2026-11-05
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# stage3-unresolved-reset

runner.py ~3698: old REVIEW_REQUIRED/NO_MATCH attempt>=2 ise aynen doner, autoresume 3 hakki bosa gider. 2026-11-05 EP04: 4 cekimden 2'si sifirlamayla PASS. Bircok cekim attempt=0 (Flash timeout ile hic onarilmamis). Parti sonrasi duzeltme: Flash/transport hatasiyla duşen cekim hakki yemesin; drive yeniden denemesi unresolved'i otomatik sifirlasin (rejected tutulur).

**Repair klasorleri:** sadece shots/N/result.json'u kenara almak yetmez; repair_1/repair_2 altindaki result.json hat tarafindan REUSE edilip ayni reddedilmis klip geri gelir (rejected.json'da olsa bile). `.`, repair_1, repair_2 uclusunu birden kenara al. attempt>=2 olan cekim sifirlanmaz. Yeni kaynak icin `recovery.search_sources_for_shots` elle cagrilabilir ama `source_recovery/empty_sentences.json`'daki cumleyi atlar; shot kopyasinda narration'i gorsel odakli bir arama cumlesiyle degistir (plan degismez), bulunani `sources/supplemental/<id>.json` assets'e ekle.
