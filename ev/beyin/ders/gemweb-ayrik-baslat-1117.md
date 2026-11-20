---
tur: ders
aciklama: gemweb :8790 Claude arka plan görevi (bekci -- komut) altında başlatılınca iz bırakmadan ölüyordu (11-16 exit 4, 11-17 exit 1); artık ayrık başlat
kaynak: oturum 238b861c 2026-11-17
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: ortak
---
# gemweb-ayrik-baslat-1117

gemweb sunucusu bekci.py -- komut ile Claude arka plan görevi içinde başlatıldığında iki kez çıktı/traceback olmadan sunucuyla birlikte kapandı (görev ağacı öldürülünce çocuk da ölüyor). Çözüm: PowerShell Start-Process -WindowStyle Hidden ile ayrık başlat (stdout bekci_log/gemweb.log, stderr gemweb_err.log), sonra bekci.py --pid <pid> --log gemweb_err.log --stall-min 0 --ram-min-gb 0 yalnız izleyici. Paylaşılan uzun ömürlü sunucular (gateway, TTS) için de aynı yol.
