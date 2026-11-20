---
tur: ders
aciklama: Avenox demo 'cakma/tatsiz' duruyordu: tek zemin+tek vurgu+tek font ailesi ile duzeldi; demo sesi yalniz son bolumdeydi
kaynak: Avenox_inceleme oturumu 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# avenox-renk-font-sistemi-1118

Sorun 1: imza_demo mux'u anlatici sesini yalniz son bolume koymustu (ilk 33 sn sessiz). Cozum: her bolume kendi sahnesinin kaynak-zaman ses dilimi (SEC listesi), gorsel ayni kaynak t'yi kullanir; volumedetect her bolumde -15..-18 dB. Sorun 2: renk/font karmasi (lacivert+kagit+turuncu+mint, Bahnschrift+Consolas) referans kanallarin yaninda cakma duruyordu. Referanslar: tek baskin zemin, karaktere bagli tek vurgu, tek font ailesi, bol bosluk. Bizim sistem: sicak komur zemin (24,20,18) + sag altta ors atesi isigi + gren, tek vurgu kor turuncusu (255,106,42 = Ors kenar rengi), metin kirik beyaz/soluk, paneller koyu sicak + ince cizgi; font yalniz Franklin Gothic (FRAHV/FRADM/FRADMCN/FRABK, Turkce tam; Rockwell/Gill/TCB'de g/s/I eksik). Resmi=kirik beyaz+tik, sahte=turuncu+X. Kod: Avenox_inceleme/araclar/imza_demo.py
