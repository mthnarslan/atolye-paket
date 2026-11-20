---
tur: ders
aciklama: Dublaj cevirisi hiz testi: Sonnet 5 paralel ajan 24 ada 43 sn, hece uyumu 22/24; GPT (oceanapi) 503/502 dalgali, dolgu uyduruyor
kaynak: testbench/dub_1107/test
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# dub-ceviri-hiz-1108

testbench/dub_1107 (Colin and Samir 'New Rules of YouTube 2027', 65 dk, 359 ada). Test 15:00-20:00, 24 ada, 5 parca x 5 ada. Sonnet alt ajan (tek gecis, Read+Write): parca 25-43 sn, 5 paralel duvar 43 sn, 6,0 hece/sn hedefinde 0,9-1,1 araliginda 22/24. GPT gpt-6.1-sol low: basarili parca 9-20 sn ama arka servis oceanapi.dev ayni parcaya rastgele 503 'temporarily unavailable'/502/504 donuyor, 6 yeniden denemede bile her kosuda 1 parca dusuyor; medium 504'e dusuyor. GPT ayrica heceyi tutturmak icin icerik ekliyor ('adam sahada cok formda', 'galibiyet') - ayni 10 adada aralik ici GPT 5, Sonnet 9. Karar: ceviri Sonnet paralel ajanlar; GPT sadece servis duzelirse yan kontrol. Whisper sistem Python'unda cublas64_12.dll yok -> os.add_dll_directory(dub_1101/omni/.venv/.../torch/lib) (src/asr_words.py); large-v3-turbo 65 dk = 333 sn.
