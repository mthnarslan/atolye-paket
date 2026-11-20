---
tur: ders
aciklama: GPT isci gorsel top-up'ta PASS dedi ama sahte Commons URL + mevcut 6 gorselin kirpma kopyalari; ayrica ilk top-up ayni Commons dosyalarini yeniden indirdi
kaynak: testbench/landmark/work/F2_stonemtn, sm_real
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# gpt-isci-sahte-gorsel-1113

Landmark 13 Kas Stone Mountain: P/F isci 'figure ekledim PASS' dedi. 1) ilk top-up: 22 source_url iki kez (ayni dosya yeni id), dhash crop'u yakalamaz -> source_url tekrar sayimi sart. 2) F2: 'Stone_Mountain_new_visual_01.jpg' gibi uydurma URL'ler, gorseller 6 kaynagin kirpma varyantlari (tuz kesiti, Sierra yol yarmasi gibi alakasizlar). Cozum: gorsel getiren iscinin ciktisini Claude grid (work/grid.py) + source_url benzersizlik + URL gercek mi (sayfa basligi aramada var mi) ile kontrol eder; az sayida gercek gorseli Claude Commons API'den seri (2 sn ara, 429'da 60 sn) kendisi ceker (USGS Bulletin 426 Stone Mountain levhalari PD). Ayrica: 5 paralel P iscisi Commons 429 -> seri calistir.
