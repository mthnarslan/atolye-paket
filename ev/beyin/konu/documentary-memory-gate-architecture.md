---
tur: konu
aciklama: Hız ve çökme arasındaki denge: işçi eşzamanlılığı API'de, bellek eşzamanlılığı medya kapısında; ölçülen bellek rakamları.
kaynak: auto-memory C--Users-meteh/memory/documentary-memory-gate-architecture.md
olusturma: 2026-10-22
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Ekranda siyah kalan kosunun kok nedeni ve cozumu (2026-10-22, `documentary_materials/resources.py`).

**Kok neden:** shot isci havuzunun genisligi havuz acilirken bir kez okunuyordu (`(bos - RESERVE_MB) // 400`); o an makine mesgulse havuz 1-2 iscide kalip kosu saatlerce suruyordu.
**Cozum - iki eszamanlilik ayrildi:** *isci* eszamanliligi API cagrisi sinirlidir (12 eszamanli API cagrisi toplam 1-3 MB), genis tutulur (15'e kadar). *Medya* eszamanliligi bellekle sinirlidir: `resources.MEDIA = MemoryGate(per_unit_mb=300, ceiling=12)`, genislik **her alimda** yeniden okunur; RESERVE_MB=1200; tarayici birimi 800 MB (`three_render._browser_limit`). `render.SLOTS` ve `runner._pool_width()` kaldirildi.
**Olculen birimler (16 GB):** Headless Chrome+node 472 MB; 1080p VIDEO render tepe 401 MB. Bos bellek 993 MB iken kapi 1, 2695 MB iken 4; makinedeki uygulamalar ~6 GB tutuyor. Docker WSL (17 konteyner 2950 MB, private commit ~7 GB) en buyuk geri kazanilabilir blok ama kullanicinin kendi yigini; pipeline kapatmaz (gereken tek konteyner searxng).
**How to apply:** Yeni medya alt sureci `subprocess.run` ile degil `resources.media_run` ile cagrilmali; havuz genisligi bellekten okunmali. Ilgili: [[documentary-shot-phase-batch-race]], [[ram-tuketiciler-1105]], [[documentary-pipeline-project]].
