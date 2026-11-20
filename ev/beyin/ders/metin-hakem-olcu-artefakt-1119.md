---
tur: ders
aciklama: Metin turnuvasi: insan korpusunda gemweb ret cevabi + dublaj; W2 dolgu temizligi Gemini'yi oynatmadi (gerekce yeni ize kayar); esit sunum + negatif kontrol + yazar x hakem gerekli
kaynak: testbench/metin_kural_1118/dil_test/kanit3/abl (tur5_*, tur6_RAPOR.md)
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# metin-hakem-olcu-artefakt-1119

Opus danisman 11-19: (1) insan5.norm() gemweb ret cevabini onbellege yaziyordu (k5/h_yWv8bPB8am4: 'Ben yalnizca bir dil modeli'), Tbog-mnt1g0 dublaj; ikisi cikinca GPT Z %59->%66, W2 %52->%59, Gemini Z 55/56. (2) Gerekce alanina gore iz yamamak ise yaramaz: W2 dolgu silindi, Gemini 59->57/64, gerekce 'hier/das Ding/sahte gorsel'e kaydi. (3) Sunum farki: orta() kisa metinde kanca+kapanisi da veriyor, insan tarafinda [Musik]/roportaj/ASR izleri kaliyor. (4) '+10' kurali CI'ye bakmiyor; metin x insan bootstrap gerek. (5) Gemini sira tutarliligi %96, GPT %77 ve ASR gurultusunu YZ sayiyor -> en sert hakem baglar. Duzeltme ajani turnuva6.py + korpus_kapi.py.
