---
tur: ders
aciklama: Kapak olculeri (kalabalik KB, kenar, puruzsuzluk, 168px okunurluk, akista saliency payi) 144 rakipte tutma carpanini ayirmiyor (hepsi p>0.19); puruz gercek/AI ayirmiyor (p=0.52): yalniz koruma bandi
kaynak: testbench/kapak_fikir/olcu/sonuc.json
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# kapak-olcu-curutme-1119

testbench/kapak_fikir/olcu.py, 29 video 144 rakip + 147 bizim kapak. Video ici Spearman olcu~log(carpan): kb rho -0.04 p0.66, kenar -0.04 p0.61, puruz -0.11 p0.19, okunur168 0.01 p0.93 (n51), dikkat(spektral saliency 2x3) -0.09 p0.27. Laplacian puruz gercek kare 2195 vs AI 1854 medyan p0.52 -> AI-gorunum olcusu degil. Arastirma (arastirma/RAPOR.md, 30 link denetli): YouTube kapak CTR'si icin hakemli kanit yok; karmasiklik ters-U (Springer 2026, 22958 kapak). Sonuc: nesnel olcu tahminci degil, rakip 10-90 bandi disi = uyari; zevk sinyali kullanicinin begenisinden. Koruma bandi: kb 9.3-26.3, kenar .04-.225, dikkat .42-1.75.
