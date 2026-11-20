---
tur: ders
aciklama: Pocket TTS 'A RAND'/'RAND study' kısaltmasını Iran/Brand okuyor; 'The RAND Corporation' + say='Rand' yaz, whisper ile doğrula
kaynak: hf/asker11/tools/vo.py
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# pocket-rand-iran-1113

asker11 L01/L18: Pocket 'RAND' -> whisper 'Iran'/'Brand'. Çözüm: cümleyi 'The RAND Corporation war-games...' yap, vo.py say alanında 'Rand'. Ayrıca vo.py print'i cp1254 konsolda 'ł' ile çöker: PYTHONIOENCODING=utf-8 (dosyalar yine yazılır). faster_whisper'a dosya yerine soundfile ile okunmuş 16k mono dizi dilimleri verilebilir.
