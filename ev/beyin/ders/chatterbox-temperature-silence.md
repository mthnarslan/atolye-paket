---
tur: ders
aciklama: Chatterbox Turbo, belgesel istemcisinin 0.35 sicakligiyla cumle basina 25-46 sn sessizlik uretir; servis kendi 0.8/0.95 ayarini kullanir
kaynak: oturum 4e0b25b1, 2026-11-05
olusturma: 2026-11-05
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# chatterbox-temperature-silence

Belirti: Jeff sesi (Chatterbox :7864) her cumlede %97-100 sessizlik uretti, ses 2 kat uzun, EP04 text_completeness FAIL. Sebep: documentary_voice_engine SYNTH_SETTINGS temperature 0.35/top_p 0.85 (Sopro/Pocket icin) Chatterbox'a gidiyordu; 0.35 -> 24-46 sn sessiz, 0.8 -> 2.5-5.5 sn normal. Cozum: chatterbox_serve.py istemci sicakligini yok sayar (CHATTERBOX_TEMPERATURE=0.8, TOP_P=0.95), cumle kelime basina 0.75 sn+1.5 sn'den uzunsa baska seed ile 3 kez dener; INFO'ya ayarlar eklendi (onbellek anahtari degisir). Servis uzun calismada bellek sizdirir (~160 MB/dk); kopru her filmin sesinden sonra kapatir. Ders: yeni ses motorunu tam filmden once mini filmde text_completeness + sure/kelime ile olc.
