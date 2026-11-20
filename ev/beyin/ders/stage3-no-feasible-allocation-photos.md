---
tur: ders
aciklama: Stage 3 'No feasible narrative/category allocation' = foto havuzu bos (SearXNG 8 sn timeout); once fotograf ekle
kaynak: Engineered batch 1105, docs/ARCHITECTURE_40_PER_DAY.md:200,386; Engineered batch 1105 EP05
olusturma: 2026-11-05
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# stage3-no-feasible-allocation-photos

2026-11-05 EP04 Greenfield: SearXNG :8888 ReadTimeout (8 sn) -> archive_manifest.json hic olusmadi, havuz 1 foto; PHOTO+CARD %25 (~44 kare) karsilanamaz, MILP infeasible. Video yeterli oldugu icin genisleme turu foto aramaz -> retry ayni sekilde duser. Cozum: (1) manifest yoksa once sources.fetch_archive_photos(<overview topic, events.jsonl searxng_unavailable query>, 03_materials, wanted=24) ile ayni sorguyla taban havuzu kur, (2) tools/seed_photos.py <03_materials> 'konu sorgulari'... (8 sorgu -> 104 foto, ~1,5 dk), catalog.json silinir, stage 3 yeniden. Oran gevsetilmez.

## 2026-11-05 (claude)

2026-11-05 EP05: SearXNG yaniti 10,8 sn, searxng_images varsayilan timeout=8 -> 0 foto. fetch_archive_photos(timeout=) sadece indirme icin; arama icin searxng_images.__defaults__ timeout'unu 45 yap (monkeypatch) sonra seed_photos.py. seed_photos'u 'timeout' ile sarma: sonda manifest yazdigi icin oldurulurse dosyalar inip manifest yazilmaz. Git-bash'ten Python'a /c/Users/... yolu verme (C:\c\Users olur), Windows yolu kullan. Kalici cozum (parti sonrasi): searxng timeout 8 -> 30 + yeniden deneme.


**Ilk sorgu timeout:** SearXNG her filmin ilk uzun baslik sorgusunda bir kez ReadTimeout verir (soguk motor), sonrasi 1-2 sn; `sources.searxng_images` timeout'ta 25 sn ile bir kez yeniden dener (fd8499c), diger hatalarda yeniden deneme yok.
