---
tur: ders
aciklama: KINGMAKERS km6: GPU dolunca ncnn upscale tamamen siyah jpg verdi (10 gorsel); stat kartinda sahne no 'n' degeri ezdi
kaynak: km6 2026-11-17
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: 
---
# km6-siyah-upscale-stat-n-1117

1) realesrgan-ncnn-vulkan 4 GB GPU dolu iken (G-Labs ic upscale + 2 ncnn) hata vermeden ortalama 0 piksel siyah jpg yazdi; dosya var oldugu icin hat bekleyip devam etti, filmde siyah sahne cikti. Kontrol: tum img/*.jpg mean<8 tara, png'den yeniden buyut. upfast'a cikti parlaklik kontrolu eklenmeli. 2) km.py timeline her sahneye 'n'=sira no yazar; plan stat karti degeri de 'n' ('6,000') -> kartta 16/14/71 cikti. Cozum: km.py 'val' alaninda asil degeri saklar, cards.py val'i basar. Ilk biten filmi kare panosu (fps=1/30 tile) ile gozle kontrol etmek ikisini de yakaladi.
