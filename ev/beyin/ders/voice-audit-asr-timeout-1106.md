---
tur: ders
aciklama: 4 film paralelken stage 1 ses denetimi UNVERIFIED (TimeoutExpired): yerel CPU ASR 300 sn sinirini asiyor; tek basina 224 sn
kaynak: fullrun_1106
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# voice-audit-asr-timeout-1106

EP03 (fullrun_1106) stage 1 3765 sn sonra UNVERIFIED, error_type TimeoutExpired, total 319 sn: documentary_voice_audit.transcribe_full yerel faster-whisper alt surecine timeout=300 veriyor, 4 film + render CPU'yu doldurunca asiyor. drive.py audit-only rerun yapiyor; 2. denemede ASR 224 sn'de bitti. Cozum: kopruyu DOCUMENTARY_REMOTE_ASR=<vds ssh hedefi> ile baslatmak (VDS base.en int8, /opt/offload) ya da sesleri tek tek bitirip denetimi ayni anda 4 filme yigmamak.
