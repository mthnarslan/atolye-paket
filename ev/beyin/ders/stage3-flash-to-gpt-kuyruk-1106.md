---
tur: ders
aciklama: Aşama 3: FLASH_TO_GPT=1 + GPT_SLOTS=8 Flash işini (grid_prefilter, precheck) 4 eşzamanlı GPT kuyruğuna itiyordu; io/governor/profil sıcak /reload ile kod imzasına dokunmadan değişir
kaynak: Engineered oturumu 6 Kas 16:45
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# stage3-flash-to-gpt-kuyruk-1106

Ölçüm 6 Kas, 4 canlı film: grid_prefilter 171 çağrının 40'ı gpt-6-sol'e gitti (kuyruk 51 sn, önbellek p90 220 sn, Flash-low 11 sn); precheck ort. 35 sn. io.py, adaptive_governor.py, system_speed_profile.json _PRODUCTION_CODE_FILES/_STEP3_CODE/_CATEGORY_CODE içinde DEĞİL: kopyala + GET :8099/reload iki kez (io governor'dan önce yeniden yüklenir; ilk reload'da eski governor prio bilmez → io'da TypeError yedeği koyuldu, testbench/pkg_1106/hot/io.py). Sonuç: precheck Flash-low, kuyruk ~0, 6-12 sn, hata 0. G-Labs aynı ölçümde ort. eşzamanlılık görsel 0,57 video 1,31 (max 10/9), görsel p50 25 sn, video p50 103 sn: G-Labs darboğaz değil; ANIM kaybı still check reddi (%46, ~1/3'ü işaretli nesneler: ölçüm çubuğu, kadran). G-Labs isteklerinde 'Proxy: None' — proxy'ler sadece captcha/oturumda.
