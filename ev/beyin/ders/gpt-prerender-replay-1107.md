---
tur: ders
aciklama: GPT incelemesi render oncesi kaynak tablosunda: tur 2'de kaynak %88 vs render ortalamasi %90 (GPT kendiyle %96); tur 1'in %86,7'si hakem gurultusuydu; 20/20 render sonrasi ret kaynakta gorunur
kaynak: testbench/darbogaz_1107/X_gpt_prerender; testbench/darbogaz_1107/X_gpt_prerender/RESULT.md
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# gpt-prerender-replay-1107

X_gpt_prerender (testbench/darbogaz_1107/X_gpt_prerender/RESULT.md): EP02+EP03 30 REUSE VIDEO cifti kaynak karelerle (precheck_contact) ayni istemle GPT'ye yeniden soruldu. PASS->PASS 8, PASS->FAIL 2 (overlay, altyazi), FAIL->FAIL 18, FAIL->PASS 2 (icerik yargisi). Uyum 26/30=%86,7, esik %90 alti. Tasarruf EP02 ~390 sn, EP03 ~1050 sn NVENC + media_gate 150/540 sn; kesimler paralel oldugu icin duvar saati kazanci daha az. patch.diff hazir (DOCUMENTARY_GPT_PRERENDER=1, varsayilan kapali, prod'a uygulanmadi). Kanit zayif: 12/30 cekim sonradan yeniden planlanmisti, render tablosu kontrol cagrilari yapilamadi (hakem gurultusu ayrilmadi). Yeniden denenecekse: render tablosuyla kontrol ciftleri + 50+ cift.

## 2026-11-07 (claude)

Tur 2 (hiz_1107d anlik kopya, 25 GPT kayitli cift, ~105 GPT cagrisi): render tahtasi 2 kez sorulunca kayitla %92/%88, kendi kendiyle %96; kaynak tablosu kayitla %88 (fark 2 puan, sinir 3). 4/4 GPT reddini kaynakta yakaladi. Tahtalar arasi piksel farki ort 0,9/255. hiz_1107d'de render sonrasi 20 VIDEO REUSE reddi: icerik 9, altyazi 5, logo/overlay 3, siyah kenar 2, hizli kesim 1, teknik 0 -> hepsi kaynakta gorunur, render'a ozgu ret yok. Yama testbench/darbogaz_1107/X_gpt_prerender/patch.diff (DOCUMENTARY_GPT_PRERENDER=1). Windows tuzagi: os.environ[X]='' X'i siler; Flash'a sessiz yonlenen cagrilari ayikla. Tur 1: 26/30 = %86,7 (istem yeniden kurulumu + tek atis gurultusu).
