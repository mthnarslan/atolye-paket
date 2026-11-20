---
tur: ders
aciklama: sf render: asiri yuklu uzak sunucudaki parca hic geri alinmiyordu (kalan sure negatif). 8389c28: beklenenin 1.5 katini gecen parcayi bos yerel yuva yeniden render eder. Test ile prod render ayni anda a1/vds'e binmesin
kaynak: oturum 2026-11-07 aksam
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# remote-render-overdue-1107

EP03 1107 render 1270 sn: yerel 10 parca ~11 dk'da bitti, sonra vds hf_09 (beklenen ~510 sn) 1263 sn surdu, yerel yuvalar bos bekledi. Sebep: take_local 'left > 1.3*dur/local_rate' sartina bakiyordu, sure asilinca left<0. Ayrica benim Z_remote_lane testim ayni anda a1'e 3 + vds'e 1 render bindirdi (a1 load 17, 0.06 video-s/s). Kural: uzak render testi prod render yokken.
