---
tur: ders
aciklama: Köprü 1. aşama bitince stop_sopro Chatterbox'ı öldürüyordu, başka film sesteyken bile; artık başka filmin voice_progress'i aktifse kapatmıyor
kaynak: EP02-EP05 partisi 5 Kas
olusturma: 2026-11-05
guncel: 2026-11-05
yazan: claude
onay: 
etiket: 
---
# chatterbox-stop-sopro-kills-other-film

documentary_native_bridge.run_stage stage 1: engine pocket değilse next_step_allowed olunca stop_sopro() tüm chatterbox_serve süreçlerini Force kill ediyordu. Paralel filmlerde diğer filmin sesi ortasında ölüyor (5 Kas 19:41, 20:02), istemci tek retry, 60-90 sn model yükleme. Çözüm: _other_voice_active() CodexOutputs/*/voice_progress.json içinde 10 dk'dan taze ve SUCCESS/FAIL olmayan durum varsa kapatma. Ayrıca nvlddmkm Id 13/153 GPU sürücü hataları aynı saatlerde. Testbench rapor: testbench/chatterbox_stability_1105.
