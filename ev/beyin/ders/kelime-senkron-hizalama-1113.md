---
tur: ders
aciklama: Kelime zamanini karakter oranindan tahmin etme: ort 0,18 sn, en kotu 1 sn kayma; faster-whisper + sessizlik baslangicina oturt + 1 kare erken
kaynak: hf/isaac2/tools/build60.py W(), tools/align60.py
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# kelime-senkron-hizalama-1113

Isaac 60 sn: W() kelime zamanini satir icinde karakter oraniyla tahmin ediyordu; altyazi/gorsel sesten ort. 0,18 sn, en kotu 1,03 sn kaydi, kullanici 'sesi once duyuyorum' dedi. Cozum: tools/align60.py (faster-whisper small.en CPU int8, satir sinirlari +-0,15 sn, initial_prompt=satir metni, word_timestamps) -> assets/words60.json. Whisper de duraklamada yaniliyor ('That's...' 0,9 sn gec): satirin ilk kelimesi ve noktalama/duraklama sonrasi kelime silencedetect (-35 dB, d=0.08) baslangicina oturtulur; -35 dB altinda yumusak baslangicta satir baslangicina guvenilir. Gorsel 1 kare (33 ms) erken: ITU-R BT.1359 fark esigi ses once +45 ms, ses gec -125 ms; sesin once gelmesi daha kotu. Altyazilar arasi 2 kare bosluk (Netflix). Kontrol: altyazi baslangici - ses baslangici 0..-40 ms.
