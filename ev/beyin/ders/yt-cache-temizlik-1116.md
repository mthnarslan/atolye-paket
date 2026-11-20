---
tur: ders
aciklama: Belgesel yt_cache: film klasoru hard link tutar; yer acmak icin yalniz st_nlink==1 klipleri sil
kaynak: oturum 11-16 yt_cache temizligi
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: ortak,disk
---
# yt-cache-temizlik-1116

yt_cache/windows ve full'deki klipler filme hard link olarak verilir. Linkli (nlink>1) klibi silmek yer acmaz, film kopyasi kalir. 16 Kas: 12 GB'in 9,2 GB'i hicbir filmin tutmadigi kliplerdi (nlink==1, 6 saatten eski), silinince 3,2 GB kaldi. Yas olcutu (7 gun) ise yaramaz: hepsi 3 gunluktu. Kendi evict() LRU'su DOCUMENTARY_YT_CACHE_GB=20 sinirinda calisir. Komut kalibi: Python os.stat().st_nlink, .used + .index.json yan dosyalarini da sil.
