---
tur: ders
aciklama: Asama 3 cekim fazinin kuyrugu: G-Labs 3 yuva (kodda min(3)) + 15 cekim iscisi; ANIM 200-1000 sn yuva tutuyor, ucuz motion cekimleri sona kaliyor
kaynak: oturum 4e0b25b1, 2026-11-07
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# stage3-kuyruk-kilitleri-1107

Eski EP03 (old_stage3_1107): queue 491 sn, son cekim 2968 sn. Adim toplami: anim_make 9666 sn (ANIM basi 192-977 sn), render_with_qc 5814, precheck 3548, picture_fit 2288, gate 2004. 15 isci tavani (DOCUMENTARY_WORKERS yoksa flash ceiling) dolu kaliyor; ANIM isci G-Labs beklerken yuvayi tutuyor, 15 sn'lik GENERATE_MOTION cekimleri 2828-2954 sn'de basliyor. Cozum: anim.py 30fc7c3 GLABS_SLOTS tavani 10 (env DOCUMENTARY_GLABS_SLOTS=10, 25/25 hesap proxy'li, kullanici 6 Kas onayi) + kopru env DOCUMENTARY_WORKERS=24 (bekleyen isci bellek harcamaz, medya kapisi ayri). NVDEC exact sonrasi decoder %95-100 dolu, CPU %100: yerel donanim tavanda. Sunucu: ev->sunucu 0,5 MB/s oldugundan medya isi tasinmaz; sadece icerik ureten (3D render) aday. Olcum: hiz_1107c.
