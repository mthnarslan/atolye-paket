---
tur: ders
aciklama: Windows'ta runner'i taskkill /F (agacsiz) olduren cocuk render'i ve mkdir kilidini oksuz birakir
kaynak: landmark 5 film 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# runner-kill-orphans-1106

landmark 1106: lm_run.py causeway taskkill //PID //F ile olduruldu; cocuk lm_render.py calismaya devam etti (eski kod, a1/vds slot yedi, ciktisini kimse mikslemeyecekti) ve eski runner'in aldigi out/render.lock dizini kaldi -> yeni runner 25 dk lm_run.py:68'de bekledi. Cozum: her zaman taskkill //T (agac), uzak isleri pkill -f lm_lm_<v> ile temizle, mkdir kilitlerine pid yaz ve olu pid'i otomatik temizle (lm_render slot kilitleri bunu yapiyor). Teshis: py-spy dump --pid.
