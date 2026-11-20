---
tur: ders
aciklama: Desenli arka planda delogo leke birakir; periyodik dokuyu kaydirip zaman medyani temiz plaka + Poisson sinir duzeltmesi tertemiz siler
kaynak: VideoLab oturumu 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# videolab-delogo-leke-1108

VideoLab restore_engine.py: ffmpeg delogo (ve Telea inpaint) duz arka planda bile izgara/dokuyu kesip bulanik leke + kutu siniri birakti; kullanici kabul etmedi. Cozum --method clone (varsayilan): alan cevresi pencere tum karelerde okunur, zaman medyani hareketli parcacik/gurultuyu siler; dokunun periyodu otokorelasyonla olculur (izgara 80 px), ayni fazdaki temiz parca halka uyumuyla secilir, her karede karenin gercek sinir piksellerine gore Laplace (scipy splu, bir kez kurulur) ile renk farki iceri dagitilir; kareler pipe ile dogrudan libx264 CRF18 (ara mp4v yok). 8 sn 1080p ~19 sn. Kontrol: kontrasti acip (lutyuv/normalize) bolgeye bak; pay icinde gecici parcacik varsa o kenarda payi kis (--pad L T R B).
