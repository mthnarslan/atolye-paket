---
tur: ders
aciklama: Surekli GPT arastirma dongusu: 8 slot codex ajani (VDS sinirsiz), agir.py kilidi agir testleri siraya koyar, planlayici da codex ajani, PASS'e otomatik denetim gorevi
kaynak: testbench/lc_1110; ZeroPulse oturumu 2026-11-11
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# hiz-dongu-surekli-1111

11-11: Claude sef ajani isleri tur tur gonderiyordu; isciler 2-5 dk'da bitip bos kaliyordu, gorev metnindeki eski 'agir test yasak' yuzunden hepsi olcumsuz FAIL dondu. Cozum: hiz_dongu.py (slot 8, kuyruk HIZ_DONGU/kuyruk/*.json, defter HIZ_DONGU/DEFTER.md, durdurma HIZ_DONGU/DUR dosyasi) + agir.py (msvcrt kilidi + bos RAM>=2.5 GB; olcum temiz). Isci baglami dongu_baglam.md. Ilk kabul: HF_CAPTURE_PARALLEL_STREAM=true 20 sn ornekte %19-25 hizli, SSIM 0,99999, RAM +%20; tam bolum dogrulamasi kuyrukta.

## 2026-11-11 (claude)

testbench/lc_1110/hiz_dongu.py: 8 slot hep dolu; her isci tam yetkili codex exec ajani (VDS OceanAPI gpt-6.1-sol). Agir test (render/ffmpeg) agir.py kilidinden gecer: 11-11 02:00 olcumu 8 sarmalayicidan 1'i kosuyor 7'si bekliyor, RAM 1,9 GB bos. v2 (yeniden baslatinca devreye girer): planlayici duz API degil codex ajani (DEFTER+SONUC+kaniti kendisi okur, tekrari onler), PASS donen ise otomatik 'denetim_' gorevi (KARAR: KABUL/RED), onceki surecten kalan iscileri sahiplenir. Darbogaz: agir kilit tek -> toplam olcum hizi seri render hizi kadar.
