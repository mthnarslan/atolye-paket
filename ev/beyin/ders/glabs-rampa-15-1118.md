---
tur: ders
aciklama: G-Labs 15 paralel prod'da (11-18): SkullStudio common.glabs + belgesel anim.py tek havuz glabs_slot.py; rampa 4,8x
kaynak: testbench/glabs_rampa_1118/ozet.txt, sonuc.jsonl 2026-11-18; testbench/glabs_rampa_1118
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# glabs-rampa-15-1118

testbench/glabs_rampa_1118/rampa.py, 68 gorsel, hepsi 1376x768, hata 0 (UNUSUAL_ACTIVITY/Max Retries/429 yok). Seviye: 3 -> 6/6, 4,07/dk, p50 40 sn; 6 -> 12/12, 7,47/dk, p50 36; 10 -> 20/20, 10,68/dk, p50 54; 15 -> 30/30, 19,49/dk, p50 36, max 56. Kalite: ayni istemler 3 vs 15 kontak sayfa (kontak_3_vs_15.jpg) gozle esit. Ortak slot glabs_slot.py belgesel anim.py ile ayni kilit dosyalari (Belgesel_Teslim/_slots/glabs<i>.lock), toplam is en buyuk N'yi asmaz. Olculmeyen: video (omni_flash, ~290 sn) 15 paralel; gecelik ~1400 varlik sonrasi Max Retries siniri hizlaninca daha erken gelir. Prod onerisi testbench/glabs_rampa_1118/PROD_ONERI.md (SkullStudio common.glabs slot + anim.py tavan 10->15), onay bekliyor.

## 2026-11-18 (claude)

Prod 11-18: SkullStudio pipeline/common.py glabs() gonder+durum GLABS slotunda (upscale slotsuz, indirme disarda); anim.py min(15); Engineered bridge_env_1107.json DOCUMENTARY_GLABS_SLOTS=15 (kopru yeniden acilinca). Dogrulama prod_dogrula.py: 3 paralel ok, slot dolu max 3, bitiste 0. Video omni_flash 15 paralel olculmedi; gecelik Max Retries daha erken gelebilir.
