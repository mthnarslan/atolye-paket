---
tur: ders
aciklama: Drive'a GB'lik dosya yükleme: rclone remote 'gdrive' hazir (tools_dl/rclone_dl); --drive-root-folder-id ile klasore copy
kaynak: survival T6-T10 oturumu 16 Kas; survival T6-T10 16 Kas
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: ortak,drive
---
# drive-buyuk-yukleme-rclone-1116

Built-in browser'da dosya secici yok; Chrome file_upload 10 MB sinirli; drive.google.com CSP yerel fetch/iframe'i engelliyor. Calisan yol: rclone v1.76 (C:/Users/meteh/tools_dl/rclone_dl, checksum dogrulandi), remote 'gdrive' (kullanici 16 Kas izin verdi), --drive-root-folder-id <klasor id> ile alt klasore copy. Paylasilan rclone client_id 2026'da emekli olacak; kesilirse kendi client_id. config create ciktisi token basar: log'u sil. Teslim betigi testbench/survival2_1116/teslim.sh.

## 2026-11-16 (claude)

Her kanal kullanabilir: C:/Users/meteh/tools_dl/rclone_dl/rclone-v1.76.0-windows-amd64/rclone.exe copy DOSYA gdrive:ALTKLASOR --drive-root-folder-id <klasor id>. Ornek betik testbench/survival2_1116/teslim.sh (boyut kontrollu).
