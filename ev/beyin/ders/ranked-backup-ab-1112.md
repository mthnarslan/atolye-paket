---
tur: ders
aciklama: Onarımda Flash yerine sıralı yedek aday (DOCUMENTARY_RANKED_BACKUP) mini film A/B: fiziksel istek -%5, token -%4, 4 yedekten 2'si geçti; DIFF_MINI çok küçük, karar için büyük film gerek
kaynak: testbench/token_1112/ab/ab_say.py, gatebench/RB_A.json, RB_B.json
olusturma: 2026-11-12
guncel: 2026-11-12
yazan: claude
onay: 
etiket: 
---
# ranked-backup-ab-1112

testbench token_1112 commit 6c75002 (bayrak varsayılan kapalı). DIFF_MINI 2+2 koşu: A 180 fiziksel istek / 537k gerçek prompt token (-2000/istek), B 171 / 516k. Onarım Flash çağrısı A 15, B 13; yedek 4 kez kullanıldı, 2'si incelemeyi geçti. Tüm kesitler PASS (20/20 her iki taraf); FULL_PASS A 14, B 11 (küçük örnek, gürültü olabilir). DIFF_MINI'de 10 kesit, onarım az: OrcaShark gibi 334 kesit/384 onarımlık filmde etki ölçülmeli. Not: OrcaShark'ta dedektör açıkken 59 dikey/şerit onarımı kaçtı (28 beyaz, 12 bulanık, 20 siyah şerit). DIFF_MINI scene_timeline.json BOM'u silindi (yedek token_1112/ab). Sonuç dosyası shots/NNNN/result.json kökteki son durumdur, repair_* ara sonuç.
