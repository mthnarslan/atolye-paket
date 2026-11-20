---
tur: ders
aciklama: Flash gateway latency is tail-dominated (8-212 s per request); batching clip checks helps, streaming/shorter prompt/low vs high do not; keep GPT in plan race
kaynak: testbench/speed_1106/llm
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# llm-hiz-1106

1106 test (56 req): GPT gpt-6-sol plan 7 s vs Flash-high 139 s median, Flash-low 196 s, all valid; keep GPT+Flash race (Flash is the fallback). Clip check singles 8-212 s, wall set by a straggler. Batch 8 clips in 1 low call = 86 s vs 197-236 s as 8 singles, verdicts identical 20/20; a 6-clip PNG batch (8 MB) timed out at 300 s so batch with JPEG tiles, 4 per request, 120 s timeout + single fallback + 60 s hedge. Concurrency 1->6 gave only 342->197 s. Streaming and shorter system prompt: no gain. Not applied to prod; needs a mini-film A/B on JPEG tiles. Details testbench/speed_1106/llm/SPEED_LLM.md.
