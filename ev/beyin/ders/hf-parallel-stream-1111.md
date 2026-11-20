---
tur: ders
aciklama: HF_CAPTURE_PARALLEL_STREAM=true: LIMIT CLOCK tam bolum render 791->647 sn (-%18), SSIM 0.998; prod finish.py'de acik
kaynak: ZeroPulse 2026-11-11
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# hf-parallel-stream-1111

Tam bolum (493 sn, -w 3) 2+2 kosu: A 795.6/787.4 sn, B 642.9/651.6 sn, SSIM All 0.998266; 60 sn klipte ayri denetimli test %11.6. Tepe RAM B'de bir kosuda 7.1 GB. w4+bayrak tek kosu 568 sn (w3'e gore %12 daha). Isci sayisi 60 sn: w4 w3'ten %8.8 hizli, w6 daha yavas. Prod: LimitClock/lc/finish.py render oncesi os.environ.setdefault (yedek finish.py.bak_1111). Kanit testbench/lc_1110/HIZ_DONGU/018,035,039,023,024. Ders: 8 ajan tek agir kilitte bekleyince 39 dk'da sifir sonuc; 3 slot + 90 dk ile ayni isler bitti.
