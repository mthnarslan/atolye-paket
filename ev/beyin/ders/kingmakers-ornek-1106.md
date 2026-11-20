---
tur: ders
aciklama: KINGMAKERS tarzı (çizgi roman görsel + serif kart + HUD sayaç + harita) 1 dk örnek ~10 dk'da: G-Labs 8 görsel 50 sn, Pocket 19 sn, HyperFrames render 2:45 (2 işçi)
kaynak: testbench/wa_1106/RAPOR.md
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# kingmakers-ornek-1106

Şablon testbench/wa_1106: build.py (voice/durs.json -> hf/index.html + timing.json), style.css, mix.py (anlatım+ffmpeg drone+media-use bundled sfx, -15 LUFS), gen_imgs.py/gen_voice.py/up.py. Yeni konu: lines.json + görsel istemleri. Darboğaz render; RAM boşsa -w 4. letterSpacing tween'i hyperframes lint hatası (scale kullan). ffmpeg çok girişli miksde indeks = len(ins)//2. Müzik kütüphanesi yok.
