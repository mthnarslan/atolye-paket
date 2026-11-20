---
tur: ders
aciklama: Ortak araclar: Kanallar/ortak/asr.py (ASR, GPU 4-6 sn), commons.py (Commons indirici), venv_haritasi.json (modul hangi python'da); kendi kodunu yazma
kaynak: Kanallar/ortak_duzelt/W1_asr/kanit/claude_kosu*.json, W2_commons/test2, 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# ortak-araclar-1118

11-18 sorun taramasi: ayni hatalar (PyAV metadata_errors 11 sohbet, cublas 7, Commons 429 9) ders yazildigi halde tekrarliyordu; cozum araca gomuldu. (1) ASR: python C:/Users/meteh/Kanallar/ortak/asr.py ses.mp3 --json out.json [--dil tr] [--model small]; ffmpeg->numpy 16k, nvidia-*-cu12 bin klasorleri PATH+add_dll_directory ile eklenir (yalniz add_dll_directory yetmiyordu, CPU'ya dusuyordu). Olcum 34 sn mp3: GPU 4-6 sn, CPU int8 9-11 sn, iki GPU kosusu birebir ayni, CPU ile kelime benzerligi 0,97. Global Python'da av 19.0.1 -> 12.3.0 (geri alma: pip install av==19.0.1). (2) Commons: python C:/Users/meteh/Kanallar/ortak/commons.py 'File:Ad.jpg' --cikti DIR [--liste f.txt] [--genislik 1280]; API thumburl (SVG/TIFF/kucuk orijinal dogru), surecler arasi 1 istek/sn kilidi (bayat kilit 10 sn'de temizlenir), onbellek ortak/cache/commons, Retry-After>60 sn ise beklemeden dosyayi atlar (eski kod 5x60 sn kilitleniyordu: 12 dosya 300 sn'de 2 -> 24 sn'de 6, kalanlar sunucu cezasi). (3) Eksik modul: tuzak hook Kanallar/venv_haritasi.json'dan modulun kurulu oldugu python'u soyler; harita Kanallar/venv_haritasi.py ile yenilenir. (4) JSON: tek yol gemweb.json_al; isci'nin llm_json.py'si reddedildi (ilk paranteze atlayip ["start_word_id"] gibi cop donduruyordu). (5) PYTHONUTF8=1 settings env + kullanici env. (6) Bash 7,5 KB ustu komut kancasi (bash-uzun-komut-8kb-1118).
