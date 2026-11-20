---
tur: ders
aciklama: Kanallar/ortak/teslim.py (sfx_qa kapisi + tek Drive isci kuyrugu) ve Drive hizi: musteri ayari degil ag degiskenligi
kaynak: 
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# teslim-py-drive-hiz-1118

teslim.py ekle/isci/durum; kuyruk _teslim_kuyruk (TESLIM_KUYRUK ile degisir), golge modu. Drive 22 MB rclone: 8M parca 0.46/0.19 MB/s, 64M 0.49/1.14, 256M 2.24 ve 0.08 MB/s (288 sn); ayni ayarda ~28x oynama -> parca boyutu hizi belirlemiyor, ag dalgalanmasi; Drive suresini 0.1-2 MB/s araliginda planla, varsayilan --parca 64M; tek dosyada --transfers etkisiz. rclone bir kosuda dosyayi yukleyip go runtime crash kodu 2 verdi: olcut uzak boyut. sfx_qa GPU kullanmaz; Gemini adimi gemweb ses okumadigi icin API anahtarina duser (anahtar kalmadi -> cikis 2).
