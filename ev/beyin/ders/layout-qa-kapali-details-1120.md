---
tur: ders
aciklama: layout_qa kapalı <details> içeriğini yanlış çakışma sayıyor; QA'dan önce tüm details'i aç, sıfır genişlikli gizli panede değil 1280'de koş
kaynak: ortak-site tools/layout_qa.js
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# layout-qa-kapali-details-1120

ortak-site kanallar-yeni QA: gizli pane (0 genişlik) yüzlerce çakışma verdi; 1280'e alınca kalanlar kapalı details içeriğiydi (checkVisibility false). Tüm details açılıp window.__qa() çağrılınca 1280/768/320'de 0 sorun. _qa_tmp.js deploydan önce silinir.
