---
tur: ders
aciklama: SearXNG VDS'te (100.104.78.117:8888, yalniz Tailscale IP'ye bagli, docker --memory 400m, ~163 MB): yerelden daha cok sonuc, ayni hiz
kaynak: oturum 1b6742da
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# searxng-vds-1115

15 Kas: VDS'e docker.io kuruldu (daemon.json iptables false, Tailscale bozulmasin). /opt/searxng/settings.yml = PC ayarinin kopyasi, bind 100.104.78.117 port 8888. Olcum (3 sorgu): genel 46/43/50 sonuc vs yerel 29/26/24 (yerelde 1 motor yanitsiz), sure 1.1-1.9 sn vs 0.9-3.5 sn; videos 150 vs 129, images 371 vs 148. PC'de Docker yalniz searxng kosturuyor (Dify/lobechat 5 saattir kapali): Docker Desktop+WSL kapaninca ~1 GB RSS (vmmemwsl 568 + desktop 221 + backend 203 MB) kazanilir. Gecis: User env DOCUMENTARY_SEARXNG=http://100.104.78.117:8888 + koprü yeniden baslat; preflight.py 102. satir 127.0.0.1'i sabit okuyor, env'e cevrilmeli. Sonuc sayisi degistigi icin prod'a almadan once mini A/B.


**Prod'a alındı (15 Kas, kullanıcı onayı, A/B atlandı):** documentary_materials 46cf59a (SEARXNG_BASE varsayılan VDS, VDS yanıtsızsa yerel Docker başlatıp ona döner), .gemini/scripts 6a09201 (factcheck), Kanallar/preflight.py env/VDS. 54/54 test geçti; gerçek görsel sorgu 333 sonuç. Docker Desktop + WSL kapatıldı: boş RAM 6343 → 7714 MB.
