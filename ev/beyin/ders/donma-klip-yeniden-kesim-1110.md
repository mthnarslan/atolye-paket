---
tur: ders
aciklama: Teslim edilmis filmde donan klibi degistirme: kaynak pencereleri silinmis olur; yt_cache, yoksa sources._download_windows ile yeniden indir, TAM n kare kes
kaynak: wildyear_1110 oturumu 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# donma-klip-yeniden-kesim-1110

Durum (WildYear 1110): CodexOutputs/*/03_materials/sources pencere mp4'leri silinmis (8 MB kaldi), yt_cache/windows kismen budanmis. Cozum: testbench/wildyear_1110/wy_refreeze.py: film zamani = kumulatif kare/25 (bosluklar kliplerin icinde; finish.json gaps eklenirse esleme kayar), kaynak = result.json artifact source_path ya da video_qc.json source_id->catalog; dosya yoksa <id>_windows.ranges.json icindeki cache yolu; o da yoksa wy_fetch2.py prod sources._download_windows (yt_gate icinde, video basina ~10-15 sn, 60 pencere 3,8 dk). Tek basina yt-dlp --download-sections 320 sn surup format hatasi verdi. Kesim: -ss + -frames:v n, sonra ffprobe count_packets == n dogrula (ajanin -t ile kesimi 800 kare kisa cikti). Ham kaynakta BBC logosu geri gelir: 1.2 kirp+zoom sag-alta yasli; kontakt sayfasiyla goz kontrolu sart (reklam yazisi, (C) kredi, sag-alt logo, siyah serit cikti -> overrides.json).
