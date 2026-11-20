---
tur: ders
aciklama: Haiku low ile GPT/Sonnet RAM gorevleri (R9,R11,R12) kor tekrar: sayilar ham kanitla birebir, uydurma yok; ama derinlik Sonnet'in gerisinde
kaynak: testbench/ram_1115/H_R9_ffmpeg H_R11_kart_render H_R12_kapi
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# haiku-isci-denemesi-1116

16 Kas: R9 ffmpeg, R11 kart render, R12 kapi gorevleri ayni metinle Haiku (effort low, operator) ile kor kosuldu (ram_1115/H_*). Sure 3-6 dk, 50-72k token, hepsi 35 dk sinirin cok altinda. Dogruluk: her ana sayi kanit/ ham dosyayla tuttu (R9 81 kosu, R11 raw_*.json, R12 2085 olay+sim). Eksikler: R9 sadece 1080p/kisa klip olctu, 4K kaynak (asil 434-470 MB nedeni) ve footage yolunu kacirdi, R1 kanitini bulamadi; ama prod'un zaten FFMPEG_THREADS=2 kullandigini dogru yakaladi. R11 sentetik sahne kullandi, gorevde olmayan 'hiz <=%10' kosulunu uydurup FAIL dedi, --par havuzu ve renderer-process-limit'i denemedi (Sonnet: -%42, Haiku: -%33). R12 Sonnet'ten farkli ama gecerli bulgu: bbc_library kesimleri kapi disinda, yama+test yamasiz FAIL/yamali OK, 13/13 mevcut test OK. Sonuc: Haiku ham olcum/analiz/tarama icin guvenilir; varyant kapsami ve hedef yorumu gereken iste Sonnet low. Haiku'ya gorevi kontrol listesi gibi yaz (denenecek her varyant, gercek girdi yolu, basari kosulu aynen).
