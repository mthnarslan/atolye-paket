---
tur: ders
aciklama: YZ-metin eslesme testi icin insan tabani AYNI KONU + ana dil + 2022 oncesi olmali; Kurzgesagt ceviri tabanina gore yakalanma %95 -> adil tabanda %85 (KO %50)
kaynak: kanit3/abl/es3, bekci_log/eslesme2.log
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# metin-adil-taban-1119

11-18/19 testbench/metin_kural_1118/dil_test: eslesme.py (insan = Kurzgesagt ceviri altyazisi) 57/60 yakaliyor; noktalama esitleyince yine 57/60, hakem videoyu taniyor + konu farkli. insan_konu.py: yt-dlp ytsearch ile ayni konu (asker techizati), upload<2022, orijinal dil ASR (lang-orig), Kurzgesagt/ceviri haric; eslesme2.py insan parcasinin noktalama+bariz ASR hatasini gemweb ile duzeltir (kelime ayni). Sonuc 41/48=%85 (ES 9/12, PT 8/8, FR 8/8, JA 12/12, KO 4/8). Tek basina HAKEM: ayni konu insan ES 25, FR 21, JA 22, KO 25, PT 4 (Rodrigo Monteiro dogaclama vlog) medyan; bizim secilmis metinler 17-30 -> tek-metin puaninda insan duzeyi, eslesmede degil. Kalan sinyaller: birimleri hep acik yazma (KO 킬로그램), PT zorlama samimiyet ekleri (ne?, a gente), 2 cumlelik simetrik paragraf, vurucu kapanis. Not: JA tabani yukkuri (sentetik ses, insan yazimi metin). ASR hatasi duzeltilmezse hakem insan metnini ASR hatasindan taniyor.
