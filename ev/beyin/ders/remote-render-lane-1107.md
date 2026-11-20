---
tur: ders
aciklama: fullrun ikinci render seridi (Engineered ac0fb3b): yerel slot doluyken film sunucularda tek basina render eder, slot bosalinca >=%30 kaldiysa yerele gecer
kaynak: testbench/darbogaz_1107/Z_remote_lane (ro.log), 2026-11-07
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# remote-render-lane-1107

Olcum: yarismasiz sadece-sunucu render 4 parca/243 video-sn 632 sn (a1 ~0.12 video-sn/sn/slot, vds ~0.12; yukleme 14-58 sn/30 MB parca) = toplam ~0.4 video-sn/sn, yerel 2 slotun ~%75'i. Tam film sunucuda ~27 dk, yerelde 12-20 dk. Kural: yerel slottaki film sunuculari da kullanir, ancak baska film render bekliyorsa --local-only; bekleyen film --remote-only (REMOTE_LANE kilidi render_remote). Gecis: sf render oldurulur (kill_tree), sunucudaki yetim isler pkill '[j]obs/<film>/' ile durdurulur, biten parcalar yeniden kullanilir. Kapat: FULLRUN_REMOTE_LANE=0. Not: CRLF dosyada python replace icin once \r\n->\n normalize et.
