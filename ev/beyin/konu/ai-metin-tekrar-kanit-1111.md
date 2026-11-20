---
tur: konu
aciklama: AI metni neden anlasilir: kanitli katalog (tekrar/sablon odakli) + senaryoda kodla olculecekler; yasak listesi kalibi siler, ritmi bozar
kaynak: testbench/ai_metin_1111 (2026-11-11)
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# ai-metin-tekrar-kanit-1111

Kaynakli ozet (ham kanit testbench/ai_metin_1111/is/*/kanit; Claude dogruladi).
1) Asil iz tekrar/sablon, kelime degil. Shaib vd. arXiv:2407.00211: model metnindeki sozdizimi sablonlarinin %76'si on-egitim verisinde var (insan metninde %35), RLHF silmiyor. Padmakumar&He ICLR 2024: ayni isteme yazilan metinler birbirine benzesir (Rouge-L 0,20 vs 0,11). Munoz-Ortiz 2024: insan cumle uzunlugu daha yayik, model 10-30 token bandinda toplanir. Jakesch PNAS 2023: okurlar AI metnine 'tekrarli' etiketini daha cok verir (%12,7 vs %7,1). Russell/Karpinska/Iyyer ACL 2025: uzmanlarin gerekcesi %53 kelime, %36 cumle yapisi (ongorulebilir kalip). Wang vd. arXiv:2502.11614: uzman ipuclari = somut ayrinti eksigi, benzer yapi ve uzunluk, tekrar eden gecisler; hedefli istemle tespit %87,6 -> %72,5.
2) Kalip listesi kayar. Wikipedia 'Signs of AI writing': isaretleri duzeltilecek liste sayma; em dash yasaklanan modellerde virgul+nokta fazlaligi yeni isaret; AI kelime listesi her model doneminde degisiyor. humanizer issue #229 + bizim olcum: [[ai-metin-humanizer-ritim-1111]]. Antislop arXiv:2510.15061: 'not X, it's Y' bazi modellerde 6,3 kat. Boggia arXiv:2607.21498: hitabette insan 14,9, Claude 33,5 /10.000 kelime; olumlu yeniden yazim 59,9 -> 0.
3) Iz yeniden yazimdan sonra da kalir: Sun vd. ICML 2025 model kimligi %97,1; paraphrase sonrasi %91,4; ozet sonrasi %58,1 (iz icerik seciminde de var).
4) YouTube (support 1311392, 15 Tem 2025): 'inauthentic content' = sablonla yapilmis gorunen, ayni kanaldan arka arkaya izlenince tekrarli gelen icerik; AI ile senaryo duzenlemek serbest. Dedektor/perplexity kullandigina dair birincil kaynak yok.
5) Insan anlatim kurallari (NPR Training, MacAdam 2015/2017): tek cumlede tek fikir, yan cumleden kacin, konusmayacagin kelimeyi yazma, yuksek sesle oku, kelime tekrari kotu degil (tornado yerine 'twister' demek komik durur), sablon cabuk sikar, sayi yigma.
6) HN (4871 yorum, kalip adiyla): em dash 315, ton 104, not-X-but-Y 94, delve 68, tekrar/sablon 45, kadans 13. Anlatima ozel: 'AI kadansi insan okusa da duyuluyor'.
Bizim senaryoda kodla olculecekler (denetim/olc2.py): cumle uzunlugu CV, <=4 kelime ve 10-19 kelime payi, ayni kelimeyle baslayan cumle payi, bolum iskeleti (ilk cumle / emir cumlesinin konumu / hukmun son cumle olmasi), bolum kapanis kalibi, hedge /100 kelime, kaynak atif cumlesi sayisi. Eksik: insan yazimi anlatim referansi (ayni olcumle karsilastirma) ve Reddit verisi.
