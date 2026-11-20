---
tur: ders
aciklama: Teslim edilmis videoda hatali TTS cumlesini yamalama: demucs pencere + mix-voc*maske+yeni, video copy
kaynak: survival v3 duzeltmesi 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# tts-cumle-yama-1110

Arac: testbench/survival_fix_1110/tools (patch.py, verify.py, qa_win.py, sep.py). Yontem: Whisper large-v3 tam dokum -> Sonnet ajan aday listesi -> aday penceresini demucs htdemucs ile ayir (sep_lib, PYTHONPATH; sphn importu opsiyonel yapildi; cikti 44.1k -> 48k resample sart) ve vokale ikinci Whisper; iki gecis ayni hatayi duyuyorsa duzelt (28 adaydan 10 kaldi; sifir sureli tekrarlar Whisper artigi). Yama: out = mix - voc*maske(cumle) + yeni_TTS (rms eslesik); cumle disi ornekler bit bit ayni. Pocket ref = refs/<sha>_24000.f32 dogrudan /api/reference'a; ECAPA ile ref secimi (dogru ref 0.31, digerleri <=0.26). Tuzaklar: yillari yaziyla ver (Pocket rakami yanlis okuyabiliyor); yeni seste kelime tekrari olabilir (uvas uvas) -> benzerlik esigi yetmez, ardisik tekrar cezasi koy; pencere t<PAD'de negatif olmasin; Pocket 2.8 GB'ta recycle -> yeniden baslatma dongusu + tts retry. Mux ~4 dk/2 GB (disk).
