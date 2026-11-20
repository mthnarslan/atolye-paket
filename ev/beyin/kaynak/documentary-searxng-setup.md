---
tur: kaynak
aciklama: SearXNG'nin JSON uç noktası ve konteynerin ayar klasörü; foto havuzunun kilidi burada.
kaynak: auto-memory C--Users-meteh/memory/documentary-searxng-setup.md
olusturma: 2026-10-22
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Pipeline'ın foto havuzu (yol 2) bu makinedeki yerel SearXNG'ye bağlı: `http://127.0.0.1:8888/search?q={konu}&categories=images&format=json` (`sources.py::searxng_images`, `DOCUMENTARY_SEARXNG` ile değiştirilebilir).

**Servis kapalıyken pipeline sessizce fotoğraf havuzunu 13'e düşürüyor** ve PHOTO kotası (%25) ulaşılamaz oluyor. Arşiv fotoğrafı olmayan bir belgesel, gerçek arşiv fotoğrafı olan bir belgesel değildir — bu yüzden bu servis teslim kalitesinin parçası, isteğe bağlı bir ek değil.

**Konteyner `searxng` (kullanıcının kendi imajı, `searxng/searxng:latest`, yerelde zaten var):**
- Bağlantı: `127.0.0.1:8888` → `8080/tcp`.
- Ayar klasoru silinirse konteyner "bind source path does not exist" ile baslamaz (klasor + settings.yml yeniden kur).
- `settings.yml` içinde **`search.formats` içinde `json` olmalı**; varsayılan yalnızca `html` döner ve `format=json` boş gelir.
- `server.secret_key` yazılmalı, `server.limiter: false` olmalı (limiter redis gerektiriyor).

**Ölçüm (2026-10-22):** `Hyatt Regency walkway collapse` görsel araması → 149 sonuç; içlerinde Wikimedia/NARA arşiv fotoğrafları var. Pipeline'ın `fetch_archive_photos` bunları 640×400 altı ve 20 KB altı olanları eleyerek indiriyor.

İlgili: [[documentary-stale-source-duplicates]], [[documentary-three-editorial-rules]], [[documentary-pipeline-project]].
