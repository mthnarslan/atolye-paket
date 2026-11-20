---
tur: ders
aciklama: Isci 'X sikayeti N yorumda' derse regex'in neyi saydigina bak: Flash, em dash KARAKTERI gecen yorumu sikayet saydi
kaynak: testbench/ai_metin_1111/is/sikayet_hn + denetim/hn_say.py (2026-11-11)
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# isci-regex-sayimi-denetle-1111

HN taramasinda Flash iscisi 'em dash 355 yorum, staccato 120, hedging 49' raporladi. Ham veriden yeniden sayim (4871 yorum, kalibin ADIYLA anilmasi): em dash 315, not-X-but-Y 94, delve 68, bicim (madde/kalin/emoji) 54, genel/ruhsuz 49, tekrar/sablon 45, dolgu 34, hedging 17, kadans/ritim 13, staccato/kisa cumle 11, uclu liste 10. Iscinin regex'i yorumun kendisinde tire karakteri ya da genis kelime gecmesini sikayet sayiyordu. Kural: sayim iddiasinda once regex'i ve 3 ornek eslesmeyi oku; sikayet sayimi 'kalibin adini anan yorum' ile yapilir. Ayrica arama sorgulari em dash/delve icerdigi icin siralama secim yanlidir. Yeniden sayim betigi: testbench/ai_metin_1111/denetim/hn_say.py.
