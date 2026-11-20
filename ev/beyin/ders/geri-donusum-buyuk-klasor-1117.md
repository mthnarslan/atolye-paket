---
tur: ders
aciklama: VisualBasic DeleteDirectory SendToRecycleBin buyuk agacta 'Win32 modunda gecerli' / 'cagri seviyesi hatali' verir; dosya dosya DeleteFile calisir
kaynak: km6 teslim 2026-11-17
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: 
---
# geri-donusum-buyuk-klasor-1117

19 GB/5575 dosyalik km6 klasorunu Geri Donusum'e atarken [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(...,'SendToRecycleBin') bazi klasorlerde IOException verdi. Cozum: dosyalari tek tek DeleteFile ile at (0 hata), kalan bos klasoru Remove-Item ile sil. Once kota bak: HKCU BitBucket\Volume MaxCapacity (MB); kutu doluysa Windows en eski ogeleri kalici siler. rclone: bekciyi rclone --log-file'a bagla, stdout bos kalir ve bekci 15 dk'da yanlis 'takildi' der.
