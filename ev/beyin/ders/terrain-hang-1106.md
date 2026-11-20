---
tur: ders
aciklama: terrain lane render.py Playwright takılması
kaynak: landmark 1106
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# terrain-hang-1106

render.py'de chrome başlatılınca GPU/renderer çocuğu olmadan Playwright çağrısı sonsuza dek asılı kaldı (40+ dk, CPU 1 sn, çıktı yok); lane subprocess.run timeout'suz olduğu için tek render yuvasını tuttu, diğer tüm çekimler bekledi (fetch değildi; 502 US fallback normal). Çözüm: render.py'ye 240 sn ilerleme watchdog'u (os._exit), lane.py subprocess timeout=900, os.replace PermissionError retry. Teşhis: py-spy dump.
