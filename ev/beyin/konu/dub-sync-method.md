---
tur: konu
aciklama: Video dublaj sync: satir basi hiz degisikligi yasak; 6-15 sn ada yontemi (6 hece/sn, refit 0.85-1.03), OmniVoice empty_cache, respelling haritasi, Whisper P(tr)
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/dub-sync-method.md
olusturma: 2026-11-04
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Kullanici 11-03'te v2/v3 Turkce dublaji reddetti: satir satir konusma hizi degisiyor ("hizlaniyor yavasliyor"), Ingilizce terimler Turkce harflerle okunuyor. **Satir basi hiz degisikligine (speed/atempo) geri donme.**

**Yontem (11-04, kullanici "cok iyi", testbench/dub_1101: src/islands.py, isl_build.py, syl.py):** konusmayi gercek sessizliklerden (ffmpeg silencedetect -32dB d=0.22) 6-15 sn "ada"lara birlestir, her adayi slot x 6,0 hece/sn'ye gore ceviri (ses dogal ~6,4-6,5 hece/sn; 4-5 hedefi bosluk yapiyordu), ada basina tek OmniVoice cagrisi (duration=None), mixer sessizligi kirpar, max(start, onceki bitis+0.04)'e yerlestirir. Refit: konusma suresi slotun <0,85 veya >1,03'u olan adada metni hece x 0,95 x slot/sure ile yeniden boyutla. Sonuc: 121 ada, konusma payi 0,76 (orijinal 0,74), max gec 0,8 sn. Sync kaymasi TTS bas/son sessizligi + mixer boslugundandi.
**OmniVoice:** `create_voice_clone_prompt` ~4,8 GB ayirir -> sonrasinda `torch.cuda.empty_cache()` (yoksa 4 GB kartta cok yavas); num_step=16, ref 02 (ref 00 Hint aksani yapar). Aksan olcusu Whisper P(tr) (ECAPA benzerligi ayirmaz); qc eslesmesi sayi/terimlerle bozulur, ASR'yi oku. Terimler cogunlukla dogru okunur; respelling haritasi (isl_build.py PRON): Mac->Mek, Claude->Klod, YouTube->yutub. Ada ilk kelimesi bozulursa (reseed yetmez) acilisi yeniden yaz. XTTS 1-2 kelimede sacmalar.
Ilgili: [[dub-translator-claude]], [[ses-zinciri]].
