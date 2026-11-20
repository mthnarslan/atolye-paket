---
tur: konu
aciklama: Humanizer (blader/humanizer v4) kelime/noktalama izini siler ama ritmi tekduzelestirir; tekrar sorununu cozmez (olcum + issue #229)
kaynak: testbench/ai_metin_1111/humanizer_deneme, denetim/olc2.py, github.com/blader/humanizer/issues/229 (2026-11-11)
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# ai-metin-humanizer-ritim-1111

blader/humanizer v4.0.0 (yalniz istem, 26 kalip) Army Loadouts TOPIC 1 SCRIPT_EN uzerinde denendi (Sonnet, tek kosu): 47 VO satirinin 11'i degisti. Kodla olcum (denetim/olc2.py): cumle uzunlugu CV 0,67 -> 0,58; <=4 kelimelik cumle %21 -> %11; 10-19 kelime bandi %36 -> %43; 'The' ile baslayan cumle %27 -> %27; 'about' 13 -> 13; kaynak atfi 8 -> 8; round iskeleti (Round N. -> ... -> emir cumlesi son ceyrekte -> hukum son cumle) aynen kaldi; emir acilislari yeni tek tip kaliba dondu (On the scale.../Hung from the hook.../Lined up side by side...). Repo'nun kendi issue #229'u ayni seyi raporlar (hakemler dil modeli, 77/144 deneme): AI kelime izi 70->0, tipografi 60->0, ama 'uniform beat rate' 60->101, 'aphoristic closers' 38->61; tespit %100 -> %98,6. README: dedektorleri gecmeyi hedeflemez. Sonuc: yasak listesi/silici yeniden yazim tekrar sorununda yetmez; tekrar bolum/ritim duzeyinde kodla olculmeli. Wikipedia 'Signs of AI writing' de ayni kaymayi kaydeder: em dash yasaklanan yeni modellerde noktalama cesitliligi dustu, virgul+nokta fazlaligi yeni isaret oldu.
