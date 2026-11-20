---
tur: ders
aciklama: gaia_finish yeniden baslatma zinciri bellek tutar; temizlenemeyen klip otomatik ret; watchdog eski anahtar
kaynak: testbench/pantanal_1108/tools/gaia_finish.py, gaia_1108/manual0168/clean_watchdog.py, 2026-11-09
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# gaia-finish-restart-1109

1) gaia_finish icindeki subprocess.call(sys.argv) re-exec ust sureci 1-3,5 GB ile canli birakiyordu; artik _Restart istisnasi main() disinda yakalanip gc sonrasi tek re-exec. 2) temizlik 3 denemede olmayinca film rc=1 olup duruyordu (EP02 cekim 168); artik rejects.json'a 'logo temizligi olmadi' yazip komsu dolguyla yeniden kuruyor, en fazla 3 tur. 3) clean_watchdog seen sozlugu sadece jobs yoluyla anahtarlanmisti, yeni turda eski zamanlayici kaldi ve EP03'u yanlis oldurdu; anahtar (yol, mtime). 4) EP03 faster_whisper mkl_malloc cokmesi = commit limiti (clean_overlay 15 GB + test isi); test isini psutil suspend et. 5) GPU kilidi FIFO degil, bekleyen film iki kez kaybetti.
