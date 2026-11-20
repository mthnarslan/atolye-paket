---
tur: ders
aciklama: Noktali zeminde kamera kaymasi: kayma mesafesi nokta periyodunun kati olursa iki tam kare yan yana dikissiz birlesir
kaynak: Avenox_inceleme/araclar/damga_dk.py
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# pano-kayma-dikissiz-1118

Avenox/Damga v3: sahne gecisinde eski kare donuk, yeni kare canli, tam kareler kaydirilir (katman refaktoru gerekmez). Yatay W=1920=40x48, dikey 1080 periyoda bolunmuyor -> 1056=11x96 kaydir, ust 24 px ust uste biner. araclar/damga_dk.py pan().
