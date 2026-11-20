---
tur: ders
aciklama: Wrath ve Landmark kapakları aynı şablonda (Impact, sarı/beyaz, siyah kontur, sol üst): kaynak kapak.py + havuz analizi
kaynak: testbench/kapak_wrath, kapak_1117
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# kapak-tek-sablon-iki-kanal-1118

11-18 kullanıcı fark etti: iki kanalın bütün kapakları aynı yazı stili/renk. Sebep 1: testbench/kapak_1117/uret/kapak.py sabit kalıp (sarı ilk satır, beyaz ikinci, Impact, kontur 9) Landmark'ta kullanıldı, Wrath Gemini brifine de aynı tarif geçti. Sebep 2: Wrath analizi 30 rakip kapağı tek havuzda (26 kanal, karışık konu) inceledi, 4 video için tek 'farklar' listesi çıktı; video başına konu rakibi ve kanal başına görsel kimlik yoktu. Kural: her kanalın kendi tipografi/renk/yerleşim kimliği olsun; her video için o konunun rakip kapakları ayrı incelensin, boşluk oradan seçilsin.
