---
tur: ders
aciklama: Sabit uyku yoklamasi (sleep>=60, time.sleep, Start-Sleep) 21 gunde ~24 sa yedi; uzun_komut.py kancasi artik reddedip bekci.py'ye yonlendiriyor
kaynak: Kanallar/ortak_duzelt/darbogaz
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# uyku-yoklama-kanca-1118

Olcum Kanallar/ortak_duzelt/darbogaz/ZAMAN_RAPORU.md: alt ajan ici python -c sleep 10,1 sa/306, until 7,3 sa/185, for 6,7 sa/319; time.sleep(178)+log 14 kez 2,23 sa. Ayrica on planda >5 dk arac 21 sa/147 (hepsi run_in_background degil). Kanca ~/.claude/hooks/uzun_komut.py Bash+PowerShell: >=60 sn sabit uyku, run_in_background degilse ve bekci.py yoksa deny. tuzak sleep-bekci kurali silindi (araca gomuldu).
