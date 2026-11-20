---
tur: ders
aciklama: NBP duz gri zeminli karakter pozunu seffaf PNG'ye cevirme: kenardan baglanti + ic buyuk zemin adacigi
kaynak: Avenox_inceleme/karakter/kes.py
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: 
---
# nbp-poz-kesim-1117

G-Labs nano_banana_pro'dan duz #D9D9D9 zeminli poz isteyip cv2 ile kesmek calisiyor (Avenox_inceleme/karakter/kes.py). Yalniz kenara degen zemin silinirse kollar arasinda kapali zemin (tabela pozu) kaliyor; ek olarak tolerans<8 ve alan>%0.4 olan ic zemin adaciklari da silinmeli. Kalin koyu kontur temiz kenar veriyor.
