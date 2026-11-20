---
tur: ders
aciklama: Kapak tek basina puanlansa da (merak/tik/tik+baslik) LLM ayni kanalin cok/az tutanini ayiramadi: AUC 0.50/0.39/0.41
kaynak: testbench/kapak_puan/pilot_out.json
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# kapak-mutlak-hakem-1118

18 Kas: hakem_mutlak.py (testbench/kapak_puan) her kapagi tek basina, 4 boyutlu kolajla, hydrogen high ile puanladi. Gecerlilik: ayni kanal guclu vs kontrol_es ciftleri (olcum2.json). Sonuc (kucuk n, 9-13 cift): merak 0.50, tik 0.39, tik_t 0.41. Onceki yan yana izgara %38, ikili %39. Yani LLM ile kapak tiklama tahmini su an GECERSIZ; kapak secimini LLM puanina baglama. 609 istek basinca gemweb hesaplari TimeoutError + dinlenmeye dustu: kapak hakemi testi <=60 istek, kanal basi <=4 paralel.
