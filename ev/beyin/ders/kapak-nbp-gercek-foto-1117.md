---
tur: ders
aciklama: Gercek foto + G-Labs NBP kapak: referansi once 16:9 kirp (yoksa siyah serit), fark-maskesiyle gercek pikselleri geri koy (%64 korundu), yaziyi kendimiz bas
kaynak: testbench/kapak_1117/uret
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: ortak
---
# kapak-nbp-gercek-foto-1117

Akis: uret/commons.py (Commons foto+lisans.json) -> SkullStudio/tools/gen_variants.py (reference_images, 6 is ~2 dk, 10/10 ok) -> uret/kapak.py (fark<22 maskeyle orijinal piksel geri, Impact sari/beyaz kontur). 4:3 referans 16:9 istekte yanlara siyah serit verdi. 'Keep ... exactly unchanged, change only X' istemiyle NBP ust yarida ort. fark 15/255 (hafif yeniden cizim), maske bunu gercek fotoya dondurur. Lav kesiti gibi fantastik ekler AI belli; su alti kesiti ve havadan gorunum daha inandirici. Yazi asil unsuru ortmemeli. CC BY/BY-SA fotolarda aciklamaya atif gerekir. Ornekler testbench/kapak_1117/uret/buyuk4.jpg.
