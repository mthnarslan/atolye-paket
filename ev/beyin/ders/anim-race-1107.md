---
tur: ders
aciklama: ANIM yarisi prod'da (20ff5f2): tur basina 2 G-Labs adayi; 10 yuvada 6 zor cekim 372->270 sn, gecen 2/6->4/6, video sayisi ayni. A/B'de DOCUMENTARY_GLABS_SLOTS=10 ver (varsayilan 3, kopru 10 kullanir)
kaynak: testbench/darbogaz_1107/Y_anim_race; oturum 2026-11-07 aksam
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# anim-race-1107

pre_1107b (2 film, 50 ANIM cekim): /api/video/generate medyan 112 sn p90 162; glabs_slot bekleme medyan 0 p90 86; ANIM toplam medyan 263 sn p90 569 max 811. 22/50 cekim en az bir kez denetimden kaldi (38 klip + 28 gorsel reddi), denemeler sirali -> anim_make 400-800 sn. Flash es zamanli ort 3,5 (sinir 15) GPT 0,7 (sinir 4): API darbogaz degil. Cozum: anim.py _race, tur basina DOCUMENTARY_ANIM_RACE=2 aday paralel, ayni denetim, ilk gecen kazanir, 2 tur x 2 = en fazla 4 aday (eskisi 3 sirali). anim.py kimlige girmez (ANIM_OUTPUT_VERSION runner'da). Sahte API testi gecti; gercek A/B parti bitince. Ayni kosuda 20. dk PASS: EP02 140 (baz 78), EP03 102 (baz 32) - dc1d426 prerender + 5478439 long-first.

## 2026-11-07 (claude)

Gercek A/B (testbench/darbogaz_1107/Y_anim_race/ab.py, EP03 cekim 17,31,50,66,119,62): ilk kosu yanlislikla 3 yuvayla yapildi -> yaris 520->703 sn kotu gorundu (yuva beklemesi medyan 101 sn). Prod kopru env'inde DOCUMENTARY_GLABS_SLOTS=10; 10 yuvayla RACE=1 372 sn 2/6, RACE=2 270 sn 4/6, ikisinde 16 video. Hakem gurultusu buyuk (ayni cekim bir kosuda gecer digerinde 3 denemede kalir). Kuyruk sonlari: EP02 #91 687 sn, EP03 #169 739 sn 3 seri denemede FAIL. Kapatma DOCUMENTARY_ANIM_RACE=1. Ders: testbench'te prod ortam degiskenlerini psutil ile kopru surecinden oku.
