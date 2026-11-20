---
tur: ders
aciklama: Oracle ARM64'te hyperframes browser ensure calismaz; Playwright chromium headless shell kullan
kaynak: Engineered oturumu 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# arm-hyperframes-chrome

linux-arm64 icin chrome-for-testing yok, 'hyperframes browser ensure' hata verir; Debian chromium arm64'te cokuyor. Cozum: npx playwright install chromium-headless-shell, HYPERFRAMES_BROWSER_PATH=~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux-arm64/chrome-headless-shell (LICENSE dosyasini degil binary'yi sec). tar paketlerken --exclude=assets tum assets alt yollarini da atar; --exclude=hf_06/assets gibi tam yol ver. Hiz: lokal 2.8 sn/sn video, VDS 8, Oracle ARM -w 4 8.7 (tek cekirdek dolu). Ev->Oracle upload 0.5 MB/s, indirme 10 MB/s; VDS acik IP 3-5 MB/s up, Tailscale 0.15.
