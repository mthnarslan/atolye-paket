---
tur: ders
aciklama: Codex isci (F6) 'prod'a yazma' kuralina ragmen documentary_materials sources.py/bbc_library.py'yi prod'da degistirdi; A/B kopyasi kirlendi
kaynak: testbench/ab_1109, flash_tasarruf_1109/F6_envanter_sb
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# isci-prod-yazdi-1109

2026-11-09 flash_tasarruf F6 iscisi RESULT'ta 'Degisen production dosyalari' yazdi: prod git status ' M sources.py bbc_library.py'. Ayni saatte alinan A (prod) kopyasi da kirli oldu, A kosusu iptal edildi. Cozum: git checkout ile geri alindi, diff F6_envanter_sb/prod_written.diff'e saklandi. Kural: isci bittikten sonra HER ZAMAN prod 'git status' bak; A/B kopyasini almadan once prod'un temiz oldugunu dogrula. Ayrica testbench kopyasindaki documentary_native_bridge.py SCRIPTS yolunu sabit prod'a yazar (satir 26): kopyada Path(__file__).resolve().parent yapmazsan test prod kodunu kosar. A/B araci: testbench/ab_1109/ab.py SIDE IDX (env.json, 9router token penceresi).
