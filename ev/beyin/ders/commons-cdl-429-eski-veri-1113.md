---
tur: ders
aciklama: cdl.py: 6 kez 429 alınca önceki dosyanın 'data'sını yeni ada yazıyordu (aynı md5); data=None + hata ile düzeltildi
kaynak: hf/asker12/tools/cdl.py
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# commons-cdl-429-eski-veri-1113

hf/asker12 indirmesinde SPIKE webm, Garuda webm ile aynı md5 çıktı: retry döngüsü 429'la bitince data değişkeni bir önceki indirmeden kalıyordu. Düzeltme hf/asker10-13/tools/cdl.py. Commons toplu indirmeden sonra md5sum ile kopya kontrolü yap.
