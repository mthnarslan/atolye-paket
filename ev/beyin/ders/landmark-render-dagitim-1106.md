---
tur: ders
aciklama: Landmark 5 film: yerel parca render a1'den ~5-6x hizli; a1 darbogazi ARM x264, veryfast sart; RAM<2.5GB'de parcalar uzaga birakilir
kaynak: landmark oturumu 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# landmark-render-dagitim-1106

Olcum (2026-11-06, testbench/landmark render/lm_render.py): 30 sn parca yerelde ~85-92 sn, a1 slotunda ~550-590 sn (4 cekirdek, load ~6). Prebake/passthrough/dedup kazanc vermedi; --preset veryfast varsayilan. Slotlar out/slots mkdir kilidi (local, local_1, a1_0..2, vds_0), olu pid temizlenir; 3 film ayni anda 6 slotu paylasir. Yerel hata RAM baskisinda olur: 2 ek deneme + RAM<2.5 GB ise parca uzak slotlara. G-Labs: auth proxy listesi sadece captcha tarayicisi icin; uretim istegi 'Proxy: None' ise Google Accounts tablosunda hesap basina proxy atanmamistir (sabit atama, hesap basina ayni IP). Whisper ozel isimleri joker sayan WER ile yeniden sentez azalir.
