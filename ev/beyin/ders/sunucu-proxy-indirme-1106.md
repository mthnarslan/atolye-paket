---
tur: ders
aciklama: Oracle'dan YouTube: dogrudan bot engeli; 9router'daki 10 socks5 proxy ile cerezsiz calisiyor ~1.5 MB/s/proxy
kaynak: testbench/offload_1106/DOWNLOAD_REPORT.md
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# sunucu-proxy-indirme-1106

Oracle A1'de yt-dlp (--js-runtimes node) dogrudan 'Sign in to confirm you're not a bot'. 9router sqlite proxyPools tablosunda 10 socks5 TR proxy; hepsi calisti (10/10), cerez gerekmedi. Tek proxy ~1.45 MB/s, 4 paralel toplam 5.4 MB/s. --download-sections socks proxy ile 403: ffmpeg proxy'yi kullanmiyor -> tam dosya indir, sonra kes. a1->PC 17 MB/s. Liste a1:~/proxies.txt (600). Proxy'ler 9router ile ortak, kotali olabilir.
