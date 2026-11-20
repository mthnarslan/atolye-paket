---
tur: ders
aciklama: Almanca YZ metin dedektoru GPU denemesi: Binoculars/Fast-DetectGPT Qwen2.5-1.5B 4bit ve mDeBERTa(COLING) hepsi AUROC<0.8 -> kapi yok, silindi
kaynak: testbench/metin_ded/RAPOR.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# almanca-metin-ded-gpu-1119

Insan 162 / YZ 45 pencere (senaryolu Almanca anlatici ASR vs Gemini). Binoculars 0.34, Fast-DetectGPT 0.28 (isaret ters: insan ASR konusma dili daha tahmin edilebilir), mDeBERTa COLING sifir atis 0.531. COLING Almanca: 231 insan / 4462 gpt-3.5. 4 GB'ta ucretsiz Almanca metin dedektoru yok; olcu eslesmeli LLM hakemi (turnuva6).
