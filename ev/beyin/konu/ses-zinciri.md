---
tur: konu
aciklama: TTS dil haritasi: Ingilizce=Pocket/Jeff Chatterbox, Turkce dublaj=OmniVoice; Sopro GPU yasagi, Seed-VC dersleri
kaynak: testbench/voiceclone_1031; DURUM.md §0; scripts 102fe8a; testbench/dub_1101; dub-sync-method
olusturma: 2026-11-04
guncel: 2026-11-06
yazan: claude
onay: 
etiket: ses,tts
---
---
tur: konu
aciklama: TTS dil haritasi: Ingilizce=Pocket/Jeff Chatterbox, Turkce dublaj=OmniVoice; Sopro GPU yasagi, Seed-VC dersleri
kaynak: testbench/voiceclone_1031; DURUM.md \0; scripts 102fe8a; testbench/dub_1101; dub-sync-method
olusturma: 2026-11-04
guncel: 2026-11-04
yazan: claude
onay: 
etiket: ses,tts
---
# ses-zinciri

Ses (TTS/klon) bilgisinin ozeti, 31 Eki–4 Kas 2026. Ayrinti: `C:\Users\meteh\testbench\voiceclone_1031\` ve `documentary_materials\.claude\DURUM.md` \0.

- **Uretimde:** belgeselde Pocket TTS (:7863, `codex-repo-tests\voice-lab\Start-Pocket.ps1`). Pocket bir cumleyi tekrar ederse cumleyi yeniden yaz.
- **Jeff sesi:** Chatterbox Turbo + duygu etiketleri, kulak testinde ilk 5/5 (SIM 0,72, WER %0,7, 3,1 kelime/sn). Kullanim: `DOCUMENTARY_VOICE_ENGINE=chatterbox` (:7864) + `DOCUMENTARY_VOICE_REF=C:\Users\meteh\voices\jeff\ref.wav` (scripts 102fe8a). Ayni yol yeni izinli seslerde de gecerli. Bkz. [[voice-permissions]].
- **Sopro** (:7862) GPU'da tum filmleri dondurdu, CPU'da tut: asagidaki Sopro GPU notu. Iki agir modeli ayni anda yukleme: [[no-parallel-model-loads]].
- **Dersler:**
  - Seed-VC'ye uzun ses verme. 30 sn pencerelerle kor boler, kelime ortasindan keser. Cumle cumle donustur.
  - V2 sesi kotu cunku kaynagi 30 sn, muzikten ayristirilmis, ust bant kesik. Iyi klon icin 10+ dk temiz kayit gerekir (Jeff: 680 sn podcast).
  - Kullanicinin "Dia2'yi sevmesi" sesin farkli olmasindandi; sonra hepsini begenmedi.
- **AI ses sikayeti arastirmasi** (80 video, 690 yorum): metin AI gibi %34, telaffuz %22, tempo %14, monoton %13. Insan anlatici: cumle 6–9 kelime (bizde 14), duraklama 0,2–0,26 sn (bizde 0,48). `research_ai_voice\notes.md`.
- Dublaj: ceviriyi Claude yapar [[dub-translator-claude]], senkron [[dub-sync-method]].

## 2026-11-04 (claude)

**Dil haritasi (hangi dile hangi motor):**
- Ingilizce uretim (belgesel, ZeroPulse): Pocket TTS varsayilan; Jeff sesi Chatterbox Turbo. Bu motorlar Turkce icin kullanilmaz.
- Turkce (YouTube dublaji EN->TR, Ortak Atolye site videosu): OmniVoice (k2-fsa, Apache 2.0). Kod ve ornekler `C:\Users\meteh\testbench\dub_1101` (src/islands.py, isl_build.py). Referans ses ref 02 / Bunny; ref 00 Hint aksani yapar. Ayar: num_step=16, create_voice_clone_prompt'tan sonra torch.cuda.empty_cache() (yoksa 4 GB kart tasar). Ingilizce terimleri cogunlukla dogru okur; bazilarini yeniden yaz (Mac->Mek, Claude->Klod, YouTube->yutub; liste isl_build.py PRON). Aksan olcusu Whisper P(tr). Yontem: [[dub-sync-method]], ceviri: [[dub-translator-claude]].
- XTTS 1-2 kelimelik girdide sacmalar; Ingilizce kelimeyi ayri seslendirip araya ekleme yolu calismaz.

**Sopro GPU kilidi (10-26):** Sopro CUDA'da %100 GPU kullanirken kopru 29 thread ile `picture_fit._STATE["run"]`'u ~20 dk bekledi, TOPIC_5/7/9 olay yazmadi; Sopro olunce hemen acildi. Tek 4 GB kart SigLIP+NVENC+TTS paylasiyor. `sopro_serve.py` (`codex-repo-tests\voice-lab`) `SOPRO_DEVICE` alir, varsayilan cpu (RTF ~2,75). Sessiz kopruyu `py-spy dump --pid <kopru pid>` ile teshis et. Ilgili: [[rearm-watchers]].
