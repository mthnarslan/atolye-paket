---
tur: ders
aciklama: La Ultima Orilla T6-T10 uretiminde cozulen 8 sorun: disk dolmasi, set -e+grep, mix yavasligi, Whisper yanlis alarmlari, takilan TTS, bekci tuzaklari
kaynak: Kanallar oturumu 16 Kas survival T6-T10
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: ortak
---
# survival-uretim-dersleri-1116

16 Kas, 5 Ispanyolca survival videosu (Chatterbox ML VO -> Whisper kontrol -> edit_topic render -> ZIP -> rclone Drive).
1. DISK DOLDU: 3 ZIP (2 GB) paralel yuklenirken render ara dosyalari (_video_0..3.mp4, _video.mp4, *_mix.wav ~4 GB/film) duruyordu -> T9 concat 'No space left on device'. Kural: ZIP cikar cikmaz out/_video*.mp4 ve out/*.wav sil; yukleme dogrulaninca (Drive boyutu = yerel) ZIP + is klasorunu sil. Uzun zincirden once df ile >=3x(film+zip) bos yer bak.
2. set -e + 'cmd | grep -v X': cikti bossa grep 1 doner, betik basarili yuklemeden sonra olur. Kullan: '| { grep -v X || true; }'.
3. edit_topic.py mix(): np.convolve O(n*k) 16 dk filmde dakikalarca takiliyordu -> scipy uniform_filter1d (arac icinde, survival_1108/tools). --mux-only bayragi: parcalar hazirsa sadece mix+concat+mux.
4. Whisper yanlis alarmi: rakamlar ('1907') ve ozel isimler retake listesini sisiriyor. vo_check_topic.py norm'a num2words(es) eklendi (arac icinde). Kalan isim farklari icin GPT isci triyaji (GERCEK/WHISPER) 62->47 retake; elle bakinca 18 'kotu'nun 14'u Whisper hatasiydi.
5. Chatterbox takilan satir: max_new_tokens=1000 sabit -> ~37 dk kayip. mtl_tts.py'ye max_new_tokens param (site-packages, yedek .bak_darbogaz); cagiran taraf len(text)*12+64 sinir + ses >2x beklenen ise baska seed. Ayrinti chatterbox-token-siniri-1116.
6. Hala kotu satirlar icin: 3 yeni seed dene, Whisper ratio'su en iyi olani tut, kotuyse eskisini geri koy. Mix yapildiysa sesi tekrar karistir (--mux-only).
7. bekci: --done-regex '.' ilk satirda cikar; uzun sessiz bekleyiste (zincir onceki isi bekliyor) stall-min buyuk ver; RAM <1 GB alarminda is olmez, --pid/--log ile yeniden kur.
8. Bu ffmpeg surumu -vsync tanimiyor: -fps_mode passthrough/vfr kullan.
