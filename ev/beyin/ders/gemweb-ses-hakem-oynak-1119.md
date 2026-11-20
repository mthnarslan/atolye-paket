---
tur: ders
aciklama: gemweb ses hakemi (dinle3 tts_olasiligi) ayni dosyada tek kosuda 5 ile 94 arasi oynuyor; tek kosuya karar verme
kaynak: kanit3/ses/*_qwen_dinle*.json 19 Kas
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# gemweb-ses-hakem-oynak-1119

Qwen3-TTS FR_1: 5 ve 85; JA_1: 94 ve 8; Chatterbox FR_1 85/25/94. Ses hakemi en az 3 kosu ortancasi ister, o da gurultulu; yerel ses dedektoru (testbench/metin_kural_1118/dil_test/yerel_ses_dedektor) denetleniyor. Qwen3-TTS 0.6B Base Apache: 4 GB'ta zirve ~2.7 GB, cumle basi 16-38 sn (testbench/qwen3tts/.venv, dil_test/qwen_ses.py).
