---
tur: ders
aciklama: Chatterbox ML 4 GB GPU'da: her generate'te audio_prompt_path = VRAM tasmasi 20-50x yavas; G-Labs captcha Chrome GPU'yu paylasinca 3x yavas; cozum prepare_conditionals bir kez + empty_cache + Kaggle T4x2
kaynak: survival2_1116 oturumu 16 Kas
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# chatterbox-ml-vram-1116

RTX 3050 Ti 4 GB: Chatterbox Multilingual tek basina ~23 it/s (1,8x gercek zaman). generate(audio_prompt_path=REF) her satirda referansi yeniden kodlayinca 15 satir sonra 10-16 s/it (satir basi 280-390 sn). Duzeltme: m.prepare_conditionals(REF) bir kez, generate exaggeration ile, her satirdan sonra torch.cuda.empty_cache(); cb_full.py 3 satir ust uste >5x yavassa cikip cb_loop.sh ile taze surec acar. G-Labs captcha Chrome'lari ayni GPU'da iken yine ~6 it/s (VRAM 3,9 GB). Kaggle T4x2 (survival2_1116/kaggle, chatterbox-tts==0.1.7 + torchvision==0.21.0) 4 surecle daha hizli; yerel GPU G-Labs ile ayni anda TTS icin zayif.
