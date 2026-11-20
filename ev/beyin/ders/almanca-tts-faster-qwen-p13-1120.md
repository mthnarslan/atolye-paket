---
tur: ders
aciklama: Almanca TTS: faster-qwen3-tts 0.6B + p13 ref + paragraf basi 3 alim secimi -> tam 7 dk metinde DF Arena ort 0,023, 42/42 pencere <0,5, WER 0,05
kaynak: testbench/ses_dene/uretim
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: ortak
---
# almanca-tts-faster-qwen-p13-1120

11-20 olcum (testbench/ses_dene/RAPOR.md 'Uretim testi', uretim/skor_full_p13.json). Motor faster-qwen3-tts 0.3.2, Qwen3-TTS-12Hz-0.6B-Base, temp 1.1 top_k 100 top_p 1.0, append_silence=False, ref kesme+loudnorm -20, ref refs_yeni/p13.wav. 5_amt_v1 16 paragraf x 3 tohum, paragrafta DF en dusuk + WER<=0,08 alim. Sonuc 416,8 sn: ort 0,023, 42/42 <0,5, 3/42 insan p90 esigi (0,00019) alti, WER 0,05. Ayni ref eski HF yolunda 0,45 idi: motor yolu (faster+append_silence False+loudnorm) belirleyici, hangisi ayristirilmadi. Ref o_suc_de_2: 0,118. RTF 0,73 (4 GB RTX 3050 Ti): 10 dk ses tek alim ~7 dk, 3 alim+secim ~31-40 dk. 1.7B Kaggle'da faster yolda tek tohum 0,63 (HF 0,145): buyuk modele aktarilmadi. Uyari: secim tek dedektore gore, asiri uyum riski.
