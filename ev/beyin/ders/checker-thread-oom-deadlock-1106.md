---
tur: ders
aciklama: Arka plan kontrol thread'i istisnada olurse queue.join sonsuza bekler; RAM darliginda whisper mkl_malloc OOM verir
kaynak: landmark 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# checker-thread-oom-deadlock-1106

landmark lm_voice: faster_whisper check thread'i RAM bitince 'mkl_malloc: failed to allocate memory' ile oldu, task_done cagrilmadi, q.join 32 dk kilitlendi (CPU 0, log durgun). state.json sadece q.join sonrasi yaziliyordu -> 121 wav diskte ama state yok. Cozum: check'i try/retry (30 sn x6), wav varsa yeniden kullan (sentez yok), 20 cumlede bir checkpoint. Kural: worker thread govdesi try/finally task_done; uzun dongude ara kayit.
