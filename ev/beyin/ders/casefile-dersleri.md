---
tur: ders
aciklama: Case File (cf.py) dersleri: contact sheet tile, gorsel klip kontrolu (clip_check), ilk render hatalari (plan onbellegi, MEMORYSTATUSEX, fade d=.35, kesik belge satiri)
kaynak: Engineered oturumlari 5-6 Kas (cf.py, cf_common.py)
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# casefile-dersleri

Case File (Engineered/cf.py, cf_common, cf_build) dersleri:
- **Contact sheet:** ffmpeg `fps=1/10,tile` kisa kaynakta 2 kare basiyordu; kareleri tek tek `-ss` ile alip PIL ile dosemek (cf.py contact_sheets, 6 sayfa 18 sn). Yeni sayfalar EP04'te watermark, KCCI bug, PH karti, bos belgeyi gosterdi; eski QA gormuyordu. 10 sn ornek daktilo kartlarini yarim yakaliyordu -> kartlar bitmis halde orneklenir.
- **Gorsel klip kontrolu:** boru hatti hakem metni filigran/TV grafigini kacirir; `cf_common.clip_check` (3 kare Flash, onbellekli) EP04'te 72 klipten 34'unu isaretledi. Sira: Flow klibi > temiz yedek klip (40 sn uzakta tekrar) > kendi kartimiz; isaret <=%12 kenar seridindeyse kirp. Soguk onbellekte kontrol ~15 dk. Commit Kanallar 'casefile:'.
- **Ilk render hatalari:** 1) cf_plan.json baska EDL'e (satir sayisi farkli) gore kalmissa IndexError; make_plan artik satir araligi tutmayan plani yeniden cizer. 2) MEMORYSTATUSEX 7 ulonglong alan ister (tp ap tpf apf tv av ae); 5 alanla cagri basarisiz, bos RAM hep 0 okunur ve wait_ram sonsuza bekler. 3) ffmpeg fade `d=.35` kabul etmez, `0.35` yaz. 4) Pipeline MOTION/CARD klipleri kolaj icinde sablon gorunuyordu: timeline kendi kartimizla degistirir (sayi karti ya da tam cumle alinti; 30 sn'de en fazla 1 alinti, yoksa gercek klip). 5) Belge satirini 46 karakterde kesmek yarim olgu gosteriyordu: once nokta dolgusunu kisalt, sigmazsa satiri at. 6) Beyaz yan bantlar kaynak klipte gomulu; cf_build fit() kenar seritlerini kirpar, dikey klipte bulanik dolgu.
