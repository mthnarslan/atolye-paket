---
tur: ders
aciklama: GaiaTrace teslim ZIP'i: testbench/pantanal_1108/tools/gaia_zip.py, delivery.py 6 klasor duzeni, klipler son filmden segment
kaynak: 2026-11-09 oturum
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# gaia-zip-teslim-1109

gaia_finish ciktisi icin delivery.py yerine gaia_zip.py <film> <mp4>: finish.json kesit kare sayilarindan EDL, altyazi anlatim zamani + paragraf bosluklari (gaps_sec/gap_len) ile film zamanina kaydirilir, klipler son mp4 bir kez NVENC + force_key_frames + segment ile bolunur (sesli, kare sayisi EDL ile ayni). Film basina ~4 dk, ~3-3,5 GB; cikti Desktop/Channells/GAIATRACE/<film>/. 5 film 2026-11-09 paketlendi.
