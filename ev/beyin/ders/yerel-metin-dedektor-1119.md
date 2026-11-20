---
tur: ders
aciklama: Yerel YZ metin dedektorleri (Binoculars/FastDetectGPT/xlm-r) cok dilde insan-YZ ayirmiyor: noktalama esitlenince AUROC ~0.5 ya da ters
kaynak: dil_test/yerel_dedektor/kanit/skor_*.csv
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# yerel-metin-dedektor-1119

Qwen2.5-0.5B cifti Binoculars, Fast-DetectGPT, log-olasilik, bibbbu xlm-roberta. Noktalamali AUROC .75-1.0 ama bu noktalama farki (insan ASR altyazi noktalamasiz). Noktalamasiz: de .51-.76, es .15-.59, pt .20-.44, fr .20-.65, ko .32-.73; ja .86-.99 ASR artefakti. Hakem olmaz, venv silindi. Kanit: testbench/metin_kural_1118/dil_test/yerel_dedektor/RAPOR.md
