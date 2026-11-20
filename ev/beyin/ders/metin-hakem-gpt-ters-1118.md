---
tur: ders
aciklama: GPT (gpt-6.1-sol) metin hakemi insan metinlerine YZ %84 verdi, bizim metinlere %62-65: tek LLM hakemi metinde hedef olamaz, iki hakem + insan kalibrasyonu sart
kaynak: kanit3/abl/gpt_kontrol.log
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# metin-hakem-gpt-ters-1118

testbench/metin_kural_1118/dil_test/gpt_kontrol.py: 5 dil x 3 gercek insan anlatici parcasi (insan_dil altyazi) GPT hakem ort 83.7 (es 88,88,88; ja 88-94); bizim v3 A 62, silme kolu S 65. Ayni insan parcalarina Gemini hydrogen hakemi ort 10-15. Gemini'de silme kolu 39->32 kazandirdi, GPT'de fark yok. Sonuc: metin 'insanlik' puani hakeme bagli; hedef koyarken hakemi insan ornegiyle kalibre et, mutlak puani raporlama.
