---
tur: ders
aciklama: model_memory._trim_working_set hic calismiyordu: ctypes GetCurrentProcess() handle'i 32-bit int donup EmptyWorkingSet hata 6 veriyor; restype/argtypes HANDLE sart
kaynak: testbench/ram_1115/R3c_trim
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# emptyworkingset-ctypes-1115

15 Kas R3c: prod _trim_working_set (ctypes.windll.psapi.EmptyWorkingSet(kernel32.GetCurrentProcess())) donus 0, GetLastError 6 (gecersiz handle), RSS hic dusmuyor; except sessizce yutuyor. Duzeltme: kernel32.GetCurrentProcess.restype=wintypes.HANDLE; psapi.EmptyWorkingSet.argtypes=[wintypes.HANDLE]. Tipli cagri: SigLIP koprude yuklu iken RSS 2064->1 MB, bos RAM ~+850 MB (5,9->6,8 GB), private bytes ayni (sayfa dosyasina gider), sonraki 20x10 tur 0,6 sn (degismedi), skorlar kirpmasiz kontrolle birebir. Ayrica: ayni sureçte 0-2. tur ile 3+. tur arasinda 0,0069 skor kaymasi ve top-5 degisimi kirpmadan bagimsiz (GPU fp16/ilk tur); 0,004 kalite bandi bunu kapsamiyor. Kanit testbench/ram_1115/R3c_trim/kanit (ctl0.log, ctl1.log, trim_run_typed.json). Konsey: Fable E' (modeli tut + bosta kirp) secti, astra ayri surec (B) dedi; olcum E''yi destekliyor.
