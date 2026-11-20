---
tur: ders
aciklama: Kanallar/link_denetle.py: arastirma raporundaki linkleri yoklar (Wayback, soft-404), alintilari ve sayilari sayfa metninde arar; Reddit pullpush, HN Algolia, 403'te curl yedegi
kaynak: C:/Users/meteh/Kanallar/link_denetle.py
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: ortak,arastirma
---
# link-denetle-arac-1117

Kullanim: python C:/Users/meteh/Kanallar/link_denetle.py rapor.md [--json x.json] (ya da - ile stdin). Paragraf/tablo satiri icindeki URL'ler 8 paralel cekilir; ayni paragraftaki "..." (>=4 kelime) alintilar o sayfalarda birebir ya da >=%85 benzer aranir; %/$/ondalik sayilar sayfada yoksa [SAY] uyarisi. Durumlar: OK, ENG (401/403/419/429 bot engeli, uydurma degil), ARS (olu ama Wayback'te var), YOK (bulunamadi ya da soft404). Cikis 1 = YOK link ya da tutmayan alinti. 11-17 test: 2 sahte link (olu alan adi + tubefilter ay arsivine yonlenen soft-404), 1 sahte alinti, 1 sahte sayi yakalandi; 7 gercek link, 3 gercek alinti gecti; ~2-5 sn. Dersler: tubefilter gibi WordPress siteleri olmayan yaziyi 200 + ust klasore (/2026/02/) yonlendirir -> yol-oneki kurali; gdc.sonniss.com Python urllib'e 403 verir, curl acar; news.ycombinator.com Python'a 419 verir -> Algolia items API. Ceviri alinti tutmaz.
