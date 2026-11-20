---
tur: ders
aciklama: SFX montajı: cue listesini komutan yazar; silah sesi kareden ölçülen namlu alevine tek atış; Flash'a video giderken temperature:0 INVALID_MEDIA verir
kaynak: asker oturumu 2026-11-11
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# sfx-senkron-montaj-1111

ASKER 1 dk örnek (testbench/asker_1111). (1) Montajı GPT işçisine serbest bırakınca 11 cue'nun 9'una aynı boom koydu, silah sesleri yanlış saniyedeydi; 2 tur kaybettirdi. Cue listesini (zaman, ses, hizalama tepe/onset, dB) komutan baştan yazmalı (is/montaj/cues_komutan.json örnek). (2) Oyun showcase klipleri aralıklı tek atış yapar: seri ses yerine her namlu alevine rifle_single ilk vuruşu. Alevi bulmak için ROI'de kare-kare parlaklık sıçraması (gray mean diff >1.5) ya da sıcak piksel; geçişin kendi flaşını alevle karıştırma. (3) Whisper kelime başlangıcı ±150 ms kayar; librosa onset ile düzelt (kelime_hizala.py, ort. 66 ms düzeltme). (4) 9router Flash'a inline video giderken temperature:0 -> INVALID_MEDIA; parametreyi çıkar. (5) -8 dB duck altında bazı SFX duyulmadı (Flash 3/8 DUYULMADI). (6) Epidemic SFX 96-192 kHz gelir, 48k'ya çevir; çok vuruşlu dosyalarda tepe geç gelir, ilk vuruşu kırp.
