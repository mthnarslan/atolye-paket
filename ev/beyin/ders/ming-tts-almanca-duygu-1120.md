---
tur: ders
aciklama: Almanca duygulu TTS: Ming-3.0-tts-0.5B satir ici etiket ([Laughter] [Sigh] [Uhm]...) kulakta en iyi; Qwen3 etiket yapmaz, duygulu ref uzun metinde tasiyor
kaynak: testbench/ses_dene/duygu/
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: ortak
---
# ming-tts-almanca-duygu-1120

11-20: Kullanici Ming-3.0-tts-0.5B (inclusionAI, MIT, task=MULTILINGUAL language_id=German, p13 ref) tag ciktisini 'cok iyi, belli oluyor' dedi; emotion parametreli surumu begenmedi. Qwen3-TTS sozsuz ses uretmez (maintainer). Qwen 0.6B + duygulu LibriVox ref: 10 sn metin 150 sn'ye tasti, DF 0.99 pencereler. Cumle duygu/etiket isaretleyici: testbench/ses_dene/duygu/isaretle.py (gemweb hydrogen high, paragraf basi 1 istek, kelime birebir kontrolu); ilk istem cok temkinliydi (%70 ciddi/sakin), anlatici tepkili istemle 12+ duygu. Kesiklik nedeni cumle cumle uretim (uret_n.py), paragraf tek cagri.
