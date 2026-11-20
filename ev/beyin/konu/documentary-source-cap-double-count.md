---
tur: konu
aciklama: Kaynak kotası çift sayım hatası: bitmiş shot hem sonuçtan hem uçuş rezervasyonundan sayılıyordu; 6 shot öldü, film teslim edilemedi.
kaynak: auto-memory C--Users-meteh/memory/documentary-source-cap-double-count.md
olusturma: 2026-10-22
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
2026-10-22 soguk kosuda 6/130 shot `RENDER_FAILED` ("6 unresolved shots; final render blocked"). Kok neden: `runner._existing_uses()` bitmis `result.json` kullanimini **ve** `SOURCE_RESERVATIONS` ucus rezervasyonunu birlikte sayiyordu (sonuc satirinda `owner` olmadigi icin koruma tutmuyordu) -> bir kaynak 1 kez kullanilinca kotada 2 sayiliyordu (20 `source_cap_exceeded`, 13 shot). Ikinci hata: `ValueError` genel isleyicide `RENDER_FAILED` oluyor, yeniden deneme ayni aday listesiyle model ayni kaynagi seciyordu.
Duzeltme: `committed_owners` ile bir shot bir kez sayilir; `SourceCapExceeded` origin'i tasir ve yeniden denemede aday listesinden dusulur (`rejected_origins`); kural gevsetilmez.
**Ders:** kota/rezervasyon kontrolunde bitmis sonuc ve ucus rezervasyonunu tek fonksiyonda say, ikisini birden degil. Ilgili: [[documentary-three-editorial-rules]].
