---
tur: ders
aciklama: 9router YouTube URL'sini image/jpeg yolluyordu (19 sn video 22.765 token); 8623.js yamasıyla video/mp4 → 3.694 (gerçek ~1.7k). 9router güncellemesinde yeniden uygula
kaynak: testbench/token_1112/A2
olusturma: 2026-11-12
guncel: 2026-11-12
yazan: claude
onay: 
etiket: 
---
# 9router-youtube-mime-1112

Sebep: chunks/8623.js mimeType fonksiyonu http(s) image_url'i uzantıya göre seçiyor, YouTube default image/jpeg. Yama: youtube.com/youtu.be ve .mp4 → video/mp4, .webm, .mov. Yedek /opt/9router/data/db/autobak/8623.js.orig-0.5.116. Etki: mini filmde pinpoint gerçek token'ın %48'i idi → toplam gerçek token ~%44 düşer. Kontrol: testbench/token_1112/A2/medres.py (19 sn video >6k token = yama gitmiş). mediaResolution 9router'da etkisiz.


**15 Kas:** 0.5.119'a güncellendi; yama artık betikle: `ssh root@100.104.78.117 python3 /opt/9router/yama_youtube.py` (regex, değişken adından bağımsız; dosya `.next-cli-build/server/chunks/`). Güncelleme: `pm2 stop 9router; cd /opt/9router; npm install 9router@<sürüm>; python3 yama_youtube.py; pm2 start 9router`. Doğrulama medres.py: 3684 token (yama yoksa >6k). Yedek /opt/9router/autobak_9router_0.5.116.tgz. 9router yalnız Tailscale IP'sine bağlanır (127.0.0.1 curl 000 verir, normal).
