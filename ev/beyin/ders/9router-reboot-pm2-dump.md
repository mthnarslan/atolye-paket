---
tur: ders
aciklama: VDS yeniden başlayınca pm2 eski dump'tan kalkar, ecosystem env değişikliği kaybolur; env değiştirdikten sonra mutlaka pm2 save
kaynak: oturum 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# 9router-reboot-pm2-dump

2026-11-06: VDS 04:17'de yeniden başladı (kernel 6.8.0-147). pm2 4 Kasım dump'ından kalktı, FETCH_CONNECT_TIMEOUT_MS=240000 yoktu → yine 60 sn sınırı, her uzun istek 249 sn sonra 502 'fetch connect timeout', sohbetler ağırlaştı. Çözüm: pm2 start ecosystem.config.cjs --update-env + pm2 save --force (dump'ta 240000 doğrulandı). 10 paralel 10/10. Kural: ecosystem env değiştirince hemen pm2 save; yavaşlık şikayetinde önce 'uptime' ve 'pm2 env 0 | grep FETCH' bak.
