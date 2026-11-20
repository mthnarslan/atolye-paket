---
tur: ders
aciklama: Animasyon kanalina gercek YouTube b-roll: proxy indir, Flash hakem stil kelimelerini yok saysin ve cömert eslesme; logolu klibi reddetme, kirp-zoom/LaMa ile temizle
kaynak: ZeroPulse LimitClock oturumu 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# limit-clock-gercek-kesit-1110

LimitClock lc/realcut.py: bu PC YouTube'dan ~40 KB/s (kisitli); .priv/proxies.txt socks rotasyonu ile 1-2 MB/s, tam dosya indir (download_ranges ffmpeg proxy kullanmaz). Flash hakem: ink/line-art gibi stil kelimelerini yok saymazsa gercek goruntuyu reddeder; ayrintiya takilan esleme (isik, kisi sayisi) ilk turda 52 sahnenin 19'unu dusurdu -> 'comert esleme' istemi. Kullanici kurali: logolu/yazili klibi reddetme; Flash kutu -> crop_out zoom<=1.2, olmazsa clean_overlay --jobs (GPU kilidi surecler arasi), stok lisans yazisi ve buyuk yazi yine ret. GPT ikinci kontrol (Q_epNN) yakin yuz yakaladi (ep03 hava fanusu sunucu).
