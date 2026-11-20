---
tur: ders
aciklama: SFX denetimi: Gemini'ye olayi soyleyince sahte pop'a bile 'duydum' diyor; var/yok+kayma yerel matched filter (Kanallar/sfx_qa.py), Gemini kor dinleme yalniz seviye/uyum/glitch
kaynak: Kanallar/testbench_sfxqa 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# sfx-qa-dalga-eslesme-1118

Test 11-18: Saarland orneginde sesi olmayan sahte pop'u Gemini (olay tarifli istem) 'yes ok' onayladi. Matched filter (SFX mp3 ilk 150 ms, 48k, NCC, +-0.3 sn): sentetik mixte 12 sahtenin 12'si yakalandi, gercek esik pop .7 impact .5 whoosh .45; anlatim altindaki .18 pop eslesmesi .27-.42 = duyulmuyor. Gemini kor olay dinlemesi gercek impact'i bile kacirdi (yanlis negatif) -> uyari; 40 sn genel kesit dinlemesi dikkatli (tekrar eden cumleyi buldu). Saarland orneginde 3 click + ilk whoosh mixte yok cikti. Grenzakten teslim.py kapisi --sfx-onay ile elle gecilir.
