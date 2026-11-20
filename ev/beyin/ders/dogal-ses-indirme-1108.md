---
tur: ders
aciklama: Son kurgu dogal ses: YouTube aralik indirmesi bayta bagli; pencere (32 sn) indirmek cekim basi (4 sn) indirmekten yavas (305 vs 188 sn, 19 cekim)
kaynak: testbench/gaia_1108 ep01_test
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# dogal-ses-indirme-1108

gaia_finish nat_audio: kaynak pencere dosyalari (sources/*_windows_NNN.mp4) SESSIZ (sadece video), dogal ses ayrica yt_gate ile indirilmeli. Denendi: pencerenin tamamini bir kez indirip dilimlemek -> 26 MB/143 sn tek indirme, toplam 305 sn; cekim basi aralik 188 sn. Hiz baglantidan degil bayttan (~50-500 KB/s). GAIA_NAT_WINDOW=1 ile acilir, varsayilan kapali. Iyilestirme fikri: daha dusuk bitrate ses bicimi secmek.
