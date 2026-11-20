---
tur: ders
aciklama: Yerel ses dedektoru eliya/forensics_0.3B_xlsr_wild insan-TTS'i AUROC 0.97 ayiriyor (CPU ~1 sn/klip); gemweb ses hakemi yerine siralama olcusu; MOS modelleri dogallik olcmez
kaynak: testbench/metin_kural_1118/dil_test/yerel_ses_dedektor/RAPOR.md, kanit/auroc.json
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# yerel-ses-dedektor-1119

465 parca x10 sn. Chatterbox vs insan 0.99, Qwen3-TTS 0.79-0.86; dil: es/pt/ja/ko ~1.0, fr .96-.98, de .81-.91. Ort sahte olasiligi insan .15, Qwen .50, Chatterbox .74. gemweb tts_olasiligi ile Spearman .44-.51. DistillMOS/DNSMOS TTS'e insandan yuksek MOS verir (AUROC .07/.17): dogallik hakemi olmaz. Lisans CC-BY-NC: yalniz ic olcum. Mutlak esik degil, kiyas olcusu. gemweb 'ES ses gecti' sonucu bu dedektorde gecmiyor.
