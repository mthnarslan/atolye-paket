---
tur: konu
aciklama: The AI video documentary pipeline project (YouTube→materyal→ses→FFmpeg) built in .gemini/scripts/documentary_materials; where the code, backups and outputs live.
kaynak: auto-memory C--Users-meteh/memory/documentary-pipeline-project.md; auto-memory C--Windows/memory/documentary-pipeline-project.md
olusturma: 2026-10-22
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Kullanıcının ana projesi: AI video belgesel pipeline'ı. Kod tabanı `C:\Users\meteh\.gemini\scripts\documentary_materials\` (Python) — `runner.py` (orkestrasyon), `io.py` (API motoru), `sources.py` (kaynak toplama), `planning.py` (MILP planlama), `render.py` (FFmpeg). Ayarlar `C:\Users\meteh\.gemini\scripts\system_speed_profile.json`.

API uçları: Flash → 9Router `http://100.104.78.117:20128/v1` · GPT/Codex (`gpt-6-sol`) → VDS `http://100.104.78.117:8765/v1` · Claude → 20128 (artık kullanılmıyor; kullanıcı "sonnet olmasın, hepsi GPT yapsın" dedi).

Test projesi `C:\Users\meteh\CodexOutputs\07_Hyatt_Regency_Collapse\`; pilot çıktısı `_voice_output\03_materials\pilot_120s\complete_video.mp4` (120 sn, 23 shot). Bridge `http://localhost:8099` üzerinden `/run` çağrısıyla stage 3/4 tetikleniyor.

**Why:** Bu proje çok dosyalı ve sürüm geçişleri (`*_v2.py` → canlıya kopyalama) yapıyor; hangi dosyanın aktif olduğu koddan anlaşılmıyor.

**How to apply:** Bu projeye dokunmadan önce hangi dosyanın canlı olduğunu hash ile doğrula (bak: [[pipeline-v2-deploy-regression]]). Çıktıları silmeden önce kullanıcıya sor.

Uretim paketi 19 dosya / ~8957 satir (hayalet `*_v2.py` dosyalari temizlendi).

Ilgili ders sayfalari: [[documentary-3d-render-ceiling]], [[documentary-memory-gate-architecture]], [[documentary-plan-review-deadlock]], [[documentary-sentence-end-initial]], [[documentary-source-cap-double-count]], [[documentary-searxng-setup]].
