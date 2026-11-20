---
tur: ders
aciklama: bekci.py -- npx ... Windows'ta WinError 2 verir: npx.cmd yaz; yalniz tur sonunda log basan iste --stall-min'i tur suresinden uzun tut
kaynak: documentary_materials oturumu 11-19
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# bekci-npx-cmd-1119

19 Kas: bekci.py komutu subprocess.Popen ile shell'siz baslatir; 'npx' bulunamaz (WinError 2), 'npx.cmd' calisir. kapak4k.py log'a yalniz tur sonunda yaziyordu, bekci 20 dk sessizlikte TAKILDI dedi ama is go/ klasorune yaziyordu: once cikti klasorunun mtime'ina bak, sonra --stall-min'i buyut. 4K kapaklar: 193/193 yayinda (ortak-site f0c3d84, deploy 410a75f5).
