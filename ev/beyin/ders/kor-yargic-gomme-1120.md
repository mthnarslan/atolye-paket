---
tur: ders
aciklama: Kanal 'aynı niş' yargıcı için başlık gömme (MiniLM, e5-base): deterministik, ayırt etme AUC 0,997; ama 4 çiftlik panel-altın sırası (G2) iki modelde de kaldı: başlık kalıbı ('The Real Reason/Why') konuyu bastırıyor
kaynak: kanal1120/kor_emb 2026-11-20
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# kor-yargic-gomme-1120

kanal1120/kor_emb (KURAL.md, KURAL_v2.md önceden sha'lı; emb_sonuc*.json). v1 MiniLM: K1(Y)0,414>K7(Z)0,366. v2 e5: K1 0,932 > K4/K7; e5 skorları 0,88-0,98 sıkışık (model kartı: göreli sıra önemli). 4 aday her iki modelde ESKI medyanının üstünde (v1 0,71-0,92 / eşik 0,52; v2 0,958-0,985 / 0,933) ama yargıç geçersiz sayıldı. Çalıştırma: voicelab-tr/.venv (torch 2.6 + transformers 5.2); ana python'da transformers huggingface_hub sürüm hatası verir.
