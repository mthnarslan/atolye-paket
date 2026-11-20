---
tur: ders
aciklama: Paralel karo indirmede os.replace Windows'ta PermissionError verir; hedef varsa tmp sil
kaynak: landmark 5 video 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# tile-cache-race-windows-1106

testbench/landmark/terrain fetch_geo.py+maps.py: iki thread ayni karoyu indirince tmp.replace(f) WinError 5 (hedef baska thread'de acik). Shot 3 kez dustu, lane fails dict'iyle kalici dislandi, runner sonsuza bekledi (derinkuyu T1, 40 dk kayip). Cozum: tmp adina thread id + replace OSError'da tmp.unlink. Ders: kalici dislanan is icin runner 'waiting' takilir; lane restart fails'i sifirlar.
