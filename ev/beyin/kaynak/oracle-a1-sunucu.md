---
tur: kaynak
aciklama: Oracle Always Free A1 (Frankfurt, ARM 4 OCPU/24 GB/100 GB): ssh a1 = ubuntu@<IP-gizli>; hyperframes ARM'da Playwright headless shell ile çalışır
kaynak: oturum 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# oracle-a1-sunucu

Hesap metehankahraman077 (Frankfurt). Sadece Always Free: A1 en fazla 4 OCPU/24 GB, blok 200 GB; deneme hesabının limiti 41 çekirdek gösterir ama aşarsan ücretli. API anahtarı ~/.oci/config, kurulum betiği Kanallar/Engineered/tools/oracle_a1.py (VCN+IGW+subnet+A1, kapasite yoksa AD'ler arasında yeniden dener; ilk denemede açıldı). Ağ: ev->Oracle scp ~0,5 MB/s, Oracle->ev ~10 MB/s. ARM'da 'hyperframes browser ensure' çalışmaz: npx playwright install chromium, HYPERFRAMES_BROWSER_PATH=~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux-arm64/chrome-headless-shell. İlk test: 50 sn'lik chunk -w 4 ile 435 sn (tek çekirdek dolu). VDS'e toplu kopya public IP <IP-gizli> ile (Tailscale upload 0,15 MB/s).
