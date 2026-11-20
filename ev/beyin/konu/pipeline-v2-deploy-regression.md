---
tur: konu
aciklama: Documentary pipeline planning.py MILP duzeltmeleri *_v2.py kopyasiyla ezildi, bazi patch'ler hic uygulanmadi; deploy oncesi diff/hash zorunlu
kaynak: auto-memory C--Users-meteh/memory/pipeline-v2-deploy-regression.md
olusturma: 2026-10-20
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Documentary pipeline'da (2026-10-20) `planning.py` MILP duzeltmeleri (hook penalty 500, last_resort, MIX_TOLERANCE 3.0->8.0) `Copy-Item planning_v2.py planning.py -Force` ile sessizce ezildi; bazi patch scriptleri de yazildi ama hic uygulanmadi.

**How to apply:** deploy oncesi `diff`/sha256 ile karsilastir; yeni v2 yazildiysa patch'leri v2'ye de uygula; "patch yazildi" != "patch uygulandi", hash/diff ile teyit et. Ilgili: [[documentary-pipeline-project]].
