---
tur: ders
aciklama: Asama 3 shots/*/result.json yapisi: row/asset yok, her sey artifact altinda (audio_start_sec, frame_count, source_path, source_start_sec); pencere kapsami sources/*ranges.json
kaynak: GaiaTrace EP01 HOOK 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# stage3-result-artifact-1108

result.json anahtarlari: identity, shot_digest, shot_id, status, review_mode, action, artifact, review, production_approved, attempt, rejected_ids, supplemental_manifest. artifact: path, visual_path, frame_count, audio_start_sec (zaman cizelgesi basi), origin_id ('youtube:ID' ya da archive.org URL), source_id, source_path (pencere mp4), source_start_sec (KAYNAK saniyesi), source_end_sec (pencere sonu olabilir, kesim sonu degil), source_segments, video_qc. Kesim suresi = frame_count/25. Pencere kapsami ve url: sources/<id>_windows.ranges.json ya da bbc_<hash>.ranges.json {url, windows:[{source_start,source_end,local_start,local_end,path}]}; pencereler sadece goruntu. render.render(row{frame_start,frame_end,timeline_start_sec}, asset{category,path,start,end}, audio_wav, out) ses ister (None verilirse mux'ta patlar), pencere kesimi kapsamazsa raise eder. Kullanan arac: testbench/pantanal_1108/tools/gaia_finish.py (son kurgu: nefes boslugu, dogal ses, logo temizligi).
