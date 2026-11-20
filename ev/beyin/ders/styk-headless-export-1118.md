---
tur: ders
aciklama: StykAnimate export diske: Playwright + kurulu Chrome (channel=chrome, WebGPU) + showSaveFilePicker taklidi -> 1080p transparan PNG zip
kaynak: Avenox oturumu 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# styk-headless-export-1118

Uygulama ici tarayicida Styk export'u diske dusmuyordu (styk-api-export-1117). Cozum Avenox_inceleme/araclar/styk_cek.py: playwright chromium.launch(channel='chrome', args --enable-unsafe-webgpu --use-angle=d3d11), context bypass_csp=True (CSP string eval'i engelliyor, wait_for_function string patlar). Playwright'in kendi headless shell'i 'No available adapters' (WebGPU yok) ile styk.ready olmuyor. init_script ile window.showSaveFilePicker taklit edilip yazilan blob 4 MB parcalarla base64 cekilir. Export penceresi <dialog> degil: 'PNG frames' (Transparent preset) yazisina tikla, boyut select'ini 1080 yap, 'Export PNG sequence' butonu. 10 kare 1080p 573 KB, ~40 sn. Kullanici: cop adami KENDIN cizme, Styk sitesini kullan (sabit sablon/tekrar olmasin).
