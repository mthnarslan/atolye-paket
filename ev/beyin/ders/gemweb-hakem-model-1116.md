---
tur: ders
aciklama: Gemini web (:8790) hakem probu: hydrogen low 10/10 geçer, flash-lite görselde düşer; pro takılır
kaynak: testbench/skull/judgeprobe/results/gw_*.md (16 Kas)
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# gemweb-hakem-model-1116

testbench/gemweb_1116 sunucusu (Firefox çerezli 5 Google hesabı, /u/N): ZERO PULSE görsel hakem probu (14 sayfa). flash-lite low 7/10 yakaladı, 1/4 yanlış alarm, görselde 'I seem to be encountering an error' döndürebiliyor; geçmez. gemini-4-hydrogen low 2 koşuda 10/10, 1/4 yanlış alarm, 95-122 sn (eski 9router Flash low kalitesi, ~2x yavaş), ~56 kredi/koşu. hydrogen high 9/10, 0/4, 108 sn. gemini-pro 3+ dk takıldı (sunucuda 180 sn sınır). Kredi: flash-lite metin 0, ses 0-1; hydrogen ~4/istek; hesap 2400/5 sa, 48384/hafta. Metin/ses işlerinde flash-lite hâlâ aday. Sunucuyu yeniden başlatmadan önce kullanan oturumlara haber ver (koşu bozuldu). Probu kosturan betik: judgeprobe/gw.py (probe.F'yi :8790'a cevirir, reasoning_effort ekler). bekci.py 'bash' komutunu WSL'e yollar: python betigiyle sar.

ARALIK denemesi (16 Kas, hydrogen low, 14 istek, 5 paralel): 20 sn 95-122 sn; 10 sn 74-83 sn; 5 sn 59-71 sn. 5 sn'de 6 koşu (84 istek) 0 hata, hiçbir hesap dinlenmedi. Görsel küçültme (tam JPEG, yarım JPEG/PNG) hız kazandırmadı (55-119 sn, gürültü), yarım boyda yanlış alarm 2/4'e çıktı: tam PNG kalsın. Kalite (tam PNG, 6 koşu): 54-55/60 yakalama, kaçan hep d_cutoff (6 koşunun 3'ünde), temizde 0-2/4 yanlış alarm. Eski 9router Flash low 3/3 koşuda cutoff'u yakaladı, 45-50 sn: hydrogen low ondan biraz zayıf ve ~%25 yavaş; Flash high ile aynı.
