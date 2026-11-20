---
tur: ders
aciklama: Kapak referansı: performans kapısı seçer (yaş-bandı ≥3x + kanal içi üst %10 + ≥10 karşılaştırma + 30g-2y, kanal başı 1); eşli kontrolde (65 çift) yalnız merak gücü ayırdı
kaynak: testbench/kapak_puan
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# kapak-referans-secim-1118

testbench/kapak_puan: havuz.py (1653 aday, 977 kanal) -> ilgi.py (olay/tur/uzak) -> sec2.py (konsey Fable+astra: 3x+hit2x kapısı 103/109 geçiriyordu, sıkılaştırıldı) -> olc2.py (Gemini kolaj TV+360/246/168) -> analiz_site.py -> site Kapaklar sekmesi (analiz.json). Bulgu: eşli Wilcoxon 17 özellikte Bonferroni'yi geçen tek özellik merak gücü (38'e 14); grafik eki p .02 ve yüz p .03 kazananda az (sınırda); okunurluk/karmaşa/renk ayırmıyor = taban kalite. Model tekrar tutarlılığı ±1 içinde %93-100, birebir %57-68: tek puan farkı gürültü. Ham 'izlenme/kanal medyanı' x1000+ şişer; yaş-bandı medyan + yüzdelik kullan. Referansların çoğu gerçek görüntü (AI ile birebir taklit olmaz). Araştırma: arastirma.md (Eden 2960 kapak da görsel farkı bulmadı).
