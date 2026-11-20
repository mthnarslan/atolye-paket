---
tur: ders
aciklama: realesrgan-ncnn-vulkan klasor modunda uzun partide 'vkQueueSubmit failed -4' (surucu dustu) sonrasi tum ciktilar SIYAH ama rc 0
kaynak: oturum 2026-11-19
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# realesrgan-ncnn-siyah-cikti-1119

Kapak 4K partisi (193 resim, ultrasharp-4x, -j 1:2:2): 40'tan sonra surucu dustu, kalan 153 png simsiyah, cikis kodu 0. Cozum testbench/kapak_4k/kapak4k.py: 10'luk paket, -t 256 -j 1:1:1, her cikti siyah mi kontrolu (max ortalama <3) ve 3 tura kadar yeniden deneme; siyah cikti kaydedilmez. Ders: ncnn rc'sine guvenme, ciktiyi kontrol et.
