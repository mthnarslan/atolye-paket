---
tur: ders
aciklama: Opak yazi silme: duragan/yavas cekimde ProPainter gri kafes birakir; LaMa anahtar kare + ECC homografi ile giydirme temiz (VideoLab/clean_overlay.py)
kaynak: VideoLab/clean_overlay.py, oturum 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# videolab-hibrit-lama-1108

Red Bull '#11 Philippines' (opak kirmizi, sol ust). ProPainter orman cekiminde (ust bolge 0.1-0.2 px/kare kayiyor) gri bulanik kafes birakti: yazinin arkasi hic acilmadigi icin zamansal yontemin kopyalayacagi piksel yok. Cozum clean_overlay.py: cekim bazli, orta kareye LaMa (big-lama.pt, Apache) - maske kapali (close 21) + 9x9 fazla pay + 200 px baglam (yoksa gokyuzunde cop); dolgu ECC MOTION_HOMOGRAPHY ile her kareye warpPerspective; renk duzeltmesi SADECE dusuk frekans (blur 6, nfill sigma 20) - yuksek frekansli duzeltme kaymis karelerde koyu/yesil bloklar yapti; gren eklemek (0.7) duz gokte gurultu yapti, varsayilan 0. Sonuc: yazi rengi piksel 0, x-t diliminde sicrama yok, 10 sn klip ~27 sn. Toplu: -i <klasor> -> <klasor>/clean. Yari saydam logoda (BBC) ProPainter iyiydi. ProPainter ticari olmayan lisans.
