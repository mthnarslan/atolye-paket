---
tur: ders
aciklama: Tür×dil ses toplama: demucs'u sadece seçilenlere uygula (ISLE_FAST), dakikada ~2→~10 klip
kaynak: ortak-site b9228d7
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# tur-ses-toplama-hiz-1115

YouTube'dan tür x dil ses toplarken (testbench/tur_dil_1115) her adaya demucs uygulamak GPU'yu tıkadı (başka film GPU'yu paylaşırken 2 işçi VRAM doldurup takıldı). Çözüm: isle.py ISLE_FAST=1 ile ham ses üzerinden whisper+f0+pencere seçimi, demucs yalnız Gemini'nin seçtiği kliplere (temizle.py). Hız ~2 -> ~10 klip/dk. 4,5 saatte 50 hücreden 30'u bitti; Vahşi/Tarih/Korku sıranın sonunda kaldı. Kadın ses az: uyku/reddit/mizah fr-de-pt hücreleri 0-1 kadın. Gelecek sefer hücreleri tür sırasıyla değil dil/tür karışık dağıt ki her türden bir şey çıksın.
