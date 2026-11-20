---
tur: ders
aciklama: Gemini web görsel limiti dolunca kapak v2: v1 yazısını LaMa ile sil + PIL ile yeni yazı (saniyeler)
kaynak: testbench/kapak_wrath
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# gemini-gorsel-limit-yerel-yazi-1118

11-18 Wrath kapaklarında Gemini sohbeti 12. istekte 'Limitiniz sıfırlanır sıfırlanmaz' dedi, görsel vermedi. Çözüm testbench/kapak_wrath/yerel_v2.py: v1 görselde yazı kutusunda beyaz/sarı pikselleri maskele, 15px genişlet (siyah kontur), VideoLab plate_fill.lama_fill ile doldur; sonra PIL ile yeni yazı. Gökyüzü üstünde iz kalmadı. Yazıyı yüz/özne üstüne koyma: D'de alt orta aile fotoğrafını kapattı, sağ alta alındı.
