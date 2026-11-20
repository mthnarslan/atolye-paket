---
tur: ders
aciklama: Clip-check batching (4 clips/request, JPEG, hedge) coded in cf_common.check_rows but A/B inconclusive: gateway degraded
kaynak: testbench/speed_1106/llm/BATCH_AB.md
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# clip-check-batch-1106

check_rows(batch=True) groups 4 clips per Flash-low request (640x360 JPEG tiles, 120 s timeout, 60 s hedge, single-clip fallback). A/B on 24 clips was run while the 9router gateway was degraded (trivial prompt 100 s, ConnectionReset): old path 1015 s with 16/24 unverified, batched path produced no usable batch answer -> agreement NOT measured and request budget exceeded. Run ab_batch.py new then old sequentially when a trivial prompt answers <10 s. Old clip_check silently treats persistent transport failure as unflagged.
