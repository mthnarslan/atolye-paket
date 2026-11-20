---
tur: ders
aciklama: bekci.py altinda npx degil npx.cmd yaz (WinError 2); faster_whisper'a dosya yolu degil ffmpeg->numpy ver (PyAV hatasi)
kaynak: Ornek_ZIPO 1118
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# hf-bekci-npx-cmd-1118

Windows'ta bekci.py komutu subprocess ile shell'siz baslatir: 'npx' bulunamaz (WinError 2), 'npx.cmd' calisir. faster_whisper transcribe(dosya_yolu) PyAV metadata_errors TypeError verdi; ffmpeg -f s16le -ac 1 -ar 16000 ile cozup float32 numpy vermek calisti.
