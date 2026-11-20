---
tur: ders
aciklama: Kapak insan davranisi: 1390 gercek olculmus kapakta 70+ ozellik; kanal ici hit/flop'u Holm sonrasi hicbiri ayirmiyor; konu rakiplerinde yuz/yazi/sok azligi outlier ile iliskili (yas degil)
kaynak: testbench/kapak_insan/test_sonuc.json, test_yas.json; arastirma insan/RAPOR.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# kapak-insan-davranisi-test-1119

Veri: A=564 kapak 72 kanal ayni kanal hit(>=2.5x)/flop(<=0.5x); B=826 konu rakibi 29 konu, konu ici Spearman log carpan. Ozellik: YuNet yuz, MobileCLIP2-S0 sifir-atis (sok, korku, gizem...), rapidocr yazi, renk, saliency (testbench/kapak_insan ozellik.py, test.py, test_yas.py). Sonuc: (1) A'da (kanal sabit) hicbir ozellik Holm'u gecmiyor; ham p<.05: hitte gulumseme az (24/71, p=.009), 1-3 kelime yazi hitte fazla (35/51, p=.011), 8+ kelime hitte az (7/25, p=.043). (2) B'de (kanallar arasi) yuksek outlier = yuz yok/az (rho -.16), yazi az (-.15), sok ifadesi az (-.17; yuzluyse -.27), felaket/korku az, gizem biraz fazla (+.10); yas kismi korelasyonla ayni kaliyor (Holm<.05, Stouffer z). Ama A ayni yonu gostermiyor: kanal tipi farki (ham goruntu kullanan kanallar daha cok outlier) olabilir, kapak etkisi kaniti degil. Yuz etkisi konuya gore: 29 konunun 23'unde negatif (derinkuyu -.53, janissary -.62), 6'sinda pozitif. Ders: permutasyon 1000 ile Holm 134 testte en iyi 0.134'e takilir; Stouffer z ya da daha cok permutasyon gerek. Kullanici begenileriyle uyumlu: 2-3 kelime yazi + yuzsuz ham sahne; sok yuzu, uzun yazi kacin.
