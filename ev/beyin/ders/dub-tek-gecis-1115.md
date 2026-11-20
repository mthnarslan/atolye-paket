---
tur: ders
aciklama: Dublaj tek geçiş: çeviriyi doğrudan slot hedef hecesine (slot x 6,4 x 0,92) yazdır, refit aşaması gereksiz; 10 dk video ~11 dk
kaynak: testbench/dub7_1115
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# dub-tek-gecis-1115

testbench/dub7_1115: tgt.py sent.json'dan tüm satırlara target (refit_list formülü) yazar, Sonnet çeviri ajanları TR_BRIEF.md ile 0,8-1,0 x target arası tr2.json yazar, chk3 problems 0, sonra s3_one.py (speed 0.88, mref/fref, bed, HLS, deploy). 7 video 2 sa 25 dk: ASR ~30 dk, çeviri 4-40 dk paralel, seslendirme 10 dk video başına ~11-14 dk; bozuk satır video başına 0-4. Uyarı: bekci çıktıyı log'a ancak sonunda yazar, STAGE1DONE gibi işaretlere bağlı bekleyişte log'u bekçi dışı yaz.
