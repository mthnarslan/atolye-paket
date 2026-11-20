---
tur: ders
aciklama: Kapak: sabit sablon (hep sol-ust dev yazi) yerine video basina konunun ilk 4 rakibini okut -> desen + tipografi spec (20 font, 6 stil, 6 ton); nislerin cogunda kazanan rakip YAZISIZ
kaynak: testbench/kapak_v5/gen, testbench/kapak_fremd/tik_zor_v4.log
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# kapak-rakip-deseni-1118

Kullanici 18 Kas: ayni font/renk/isik/konum/3 kelime tekrari olmasin, her kapak rakiplerden dogru okunarak kurulsun. Yol: testbench/kapak_v5/gen: rakip_desen.py (ilk 4 rakip 2x2 izgara -> hydrogen high: neden tiklaniyor, ortak desen, 2 fikir) -> tipo.py (font havuzu fonts/ Google Fonts OFL + Windows, stil stroke/shadow/glow/box/plain/3d, renkler, konum, aci, ton) -> yap_fikir6.py -> kapak_fremd/uret.py (refs=ilk 2 rakip) -> yazi6.py (YAZISIZ=1 ikiz). W1 Mara, WH1 Gatling, W2 orca gibi nislerde kazanan rakiplerin 4'unde de yazi yok: yazisiz ikiz sart. FREMD v4 sert test: 5_amt_D (DEUTSCHLAND 2030 / KEIN MENSCH IM AMT + zaman cizgisi + sira bekleyen robotlar) 4/4 birinci; rakip 'ABSCHALTUNG BLOCKIERT' (kalin yatik beyaz+kirmizi, el-kirmizi buton catismasi) digerlerini yeniyor. glow stilinde yazi rengi isikla ayni olursa okunmaz (duzeltildi). Commons API rate limit -> json degil; ara_commons.py tekrar+bekleme.
