---
tur: ders
aciklama: VDS OceanAPI 19 Kas: fiilen 2 eszamanli (upstream 429 scope=user), gpt-6.2-sol geldi (hiz 6.1 ile ayni), 6.2-astra kredisiz
kaynak: testbench/metin_kural_1118/dil_test/kanit3/abl/g61,g62/sure.jsonl; http://100.104.78.117:8765/__api/state
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# vds-gpt-esz-2-ve-62-1119

19 Kas olcum: /v1/models'te gpt-6.2-sol ve gpt-6.2-astra var; astra 402 insufficient_credits. Bos VDS'te kisa istek 6.1-sol 7,5 sn, 6.2-sol 8,2 sn; 8 paralel istek ciftler halinde biter (7,20,25,37,43,53 sn) -> fiilen 2 eszamanli (11-11'de 12 paralel 13-21 sn idi). /v1/responses ve /chat/completions ayni. Sebep: gateway /__api/state max_concurrency 4 ama upstream 2273x 429 (scope=user) + 3466x 503, gateway sessizce yeniden deniyor (31.698 sn geri cekilme). Yani 8 GPT iscisi paralel calismaz, kuyruklanir; yuksek paralellik icin gemweb (10 hesap). Gercek yazar gorevinde 6.2-sol cikti 341 vs 528 token, kalite (insan yan yana hakem) 6.1 ile ayni bant.
