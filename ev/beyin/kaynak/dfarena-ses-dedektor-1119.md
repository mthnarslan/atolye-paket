---
tur: kaynak
aciklama: DF Arena 500M V1 ses deepfake dedektörü yerelde çalışıyor: DE insan/TTS AUROC 0,999 (ham csv'den doğrulandı), bizim Chatterbox/Qwen sesimizi yakalıyor; ses kapısı olarak kullanılabilir
kaynak: testbench/ses_dedektor/RAPOR.md, df_main_ham.csv
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# dfarena-ses-dedektor-1119

Kurulum testbench/ses_dedektor/dfarena (1,75 GB, fp16 GPU, venv testbench/yerel_ses_dedektor/.venv + einops). Aynı 10 sn pencerelerde (208 insan, 257 TTS): tüm AUROC 0,992 (eski forensics 0,972); DE 0,999 (forensics 0,810); Qwen DE n=6 0,997 (forensics 0,238). Skorlar 0/1'e yapışık, FR/PT/KO insanında yanlış alarm yüksek: eşik dil başına kalibre edilmeli. Lisans non-commercial, iç ölçüm. Sonuç: bugünkü TTS sesimiz makineye karşı insan geçmiyor; ses iyileştirmesi bu ölçüyle izlenir. Rapor testbench/ses_dedektor/RAPOR.md.
