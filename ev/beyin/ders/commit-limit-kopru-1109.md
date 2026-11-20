---
tur: ders
aciklama: WinError 1455 / brotli allocate hatasi = Windows commit limiti; bos kopru 11,5 GB private tutuyordu, restart 1,9->12,7 GB
kaynak: Gaia 1109 oturumu
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# commit-limit-kopru-1109

2026-11-09 07:20 Gaia son kurgu 4 film + 6 codex iscisi: fiziksel bos RAM ~3 GB iken yt-dlp 'WinError 1455 disk bellegi dosyasi cok kucuk' ve 'brotli: unable to allocate memory' verdi, birkac cekimin dogal sesi inmedi. Kok: commit (RAM+pagefile) 63,4/65,3 GB. Asama 3 bitmis olmasina ragmen documentary_native_bridge.py 11,5 GB private (WS 13 MB) tutuyordu; clean_overlay 10,6 GB. Cozum: kopruyu kullanan drive.py yoksa Stop-Process + Start-Process python documentary_native_bridge.py (cwd .gemini/scripts, Hidden) -> health PASS, commit bos 12,7 GB. Kural: asama 3 bitince kopruyu yeniden baslat; izlemede fiziksel bos RAM degil Win32_OperatingSystem.FreeVirtualMemory bak (<4 GB alarm). Bkz [[kopru-bellek-sismesi-1108]].
