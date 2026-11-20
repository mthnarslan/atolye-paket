---
tur: ders
aciklama: PC kasmasi: IObit UninstallMonitor takili (1 cekirdek %99, ~30 MB/s G/C) + C: %94 dolu Crucial P3 (QLC, DRAM'siz) yazma gecikmesi ~190 ms; virus degil
kaynak: documentary_materials oturumu 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# pc-kasma-iobit-ssd-1110

10 Kas olcum: disk %100 kuyruk 20-50, yazma gecikmesi 192 ms, okuma 5,6 ms. UninstallMonitor.exe (IObit imzali, servisi IObitUnSvr durmus) yetkili calisiyor, normal kullanici kapatamaz. Defender tehdit kaydi yok. Cozum: UninstallMonitor'u yonetici olarak oldur / IObit Uninstaller'i kaldir; C:'de >=70 GB bos alan ac (QLC dolunca SLC onbellegi biter); yonetici PowerShell 'Optimize-Volume C -ReTrim'. Gecikme olcumu: Win32_PerfRawData_PerfDisk_PhysicalDisk AvgDisksecPerWrite delta (Get-Counter Turkce Windows'ta isimle calismaz).
