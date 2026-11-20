---
tur: ders
aciklama: OmniVoice Turkce klon: cumle basi buyuk harfli kisa cumle (Once Amerika. / Ayni is.) yutuluyor, kucuk harfle baslat; 2 kelimelik tek klip bozulur; kurulum tarifi
kaynak: testbench/asker_tr_1111/out/*/kontrol.json
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# omnivoice-turkce-klon-1111

Olcum (2026-11-11, testbench/asker_tr_1111, Turkce yayinci referansi 13.5 sn demucs vokal + large-v3 dokum): 15 cumle, secilen denemelerde ort. ECAPA benzerlik 0.58 (min 0.48), P(tr) 0.99, 6.4 hece/sn. Sorun: satir 2 kelimelik cumleyle basliyorsa ('Önce Amerika. Bir ...', 'Aynı iş. Masaların ...') ilk kelime yutuluyor/bozuluyor; 12 denemede duzelmedi (noktalama, speed=0.85, num_step=32, onceki cumleyle birlestirme hepsi basarisiz). Cozum: satiri kucuk harfle baslat ('önce Amerika. ...', 'aynı iş. ...') -> 6/6 dogru. 2 kelimelik cumleyi tek basina uretme (baska dile kayar, P(tr)=0). 'Kaskları' -> 'Kasları' okunuyor; 'Kask ları' yazinca dogru. Sayi/kisaltma okunusla yazilir (em dört a bir, a ka yetmiş dört em). Kurulum: venv --system-site-packages + pip install omnivoice demucs speechbrain, sonra venv icinden torch/torchaudio/torchvision'i kaldir (cpu surumu gelir; sistem cu124 kullanilsin). faster-whisper: PATH'e torch/lib ekle (cublas64_12.dll), sesi numpy dizisi olarak ver (av surum uyumsuzlugu). bekci'ye tam exe yolu ver, 'bash -c' WSL'e gider. Cok konusmacili yayindan referans: kelime zamanli dokum -> 3.5-15 sn ifadeler -> tek konusmacili monologu icerikten sec -> demucs vokal. Araclar: testbench/asker_tr_1111/tools (gen.py, kontrol.py, birlestir.py).
