# Acik isler (her oturum gorur; bitince --kapat)

- 2026-11-04 OpenCode Go + AMD Radeon Cloud'u 9router'a metin yedegi yapmak (abonelikten sonra) [[opencode-go-backup-lane]]
- 2026-11-04 RAM yukseltmesi (32 GB DDR4-3200 SODIMM) takilinca Windows'un gordugunu dogrula
- 2026-11-04 GPT film denemesi (gpt-6.1-sol medium vs prod) kullanici Flash yuku isterse [[gpt-model-secimi]]
- 2026-11-04 Melezleme sayfasi (yt_study/site/melezleme.html) kullanici yorumu bekliyor
- 2026-11-06 Oracle A1 bulut sunucu: kullanıcı hesabı açınca Claude kurar; render/kesim işlerini oraya aktarma denemesi (4 film bitince). VDS'e video aktarımı ~0,5 MB/s ile değmiyor.
- 2026-11-08 Belgesel prod: film_settings.json 'library': false destegi (profiles.for_run) + Gaia'da BBC archive.org kutuphanesi kapali; parti bitince commit [[youtube-oncelik-bbc-arsiv-yok]]
- 2026-11-10 14 Kas: token yeniden olcum (testbench/tokenaudit/sim.py 4 + turns.py): otomatik pay <%10, ana ort. baglam <95k mi; operator ajani yukleniyor mu; film sonuclarinda kalite dususu var mi [[token-denetimi-1110]]
- 2026-11-10 S14 merged.diff: S6 SigLIP idle=0 prod 9769e83 (15 Kas); kalan S2 restart, testbench mini film A/B sonrasi prod'a al; parti disinda [[sistem-denetimi-1110]]
- 2026-11-10 Teslim kapisi: analiz_1110/teslim/teslim_kapisi.py'yi gercek filmde kos, gaia_finish/gaia_zip sonuna cikis koduna bagla; extend/detitle ciktisina freezedetect d=0.8; klip bed'i kapatma karari (kullanici: sadece anlatici) [[sistem-denetimi-1110]]
- 2026-11-10 drive.py reaudit icerik FAIL'de donguden cik (analiz_1110/hiz diff) gercek kayitta test; SkullStudio common.py Flash reasoning_effort (analiz_1110/llm P1, hakem cagrilari judgeprobe ister) [[sistem-denetimi-1110]]
- 2026-11-13 14 Kas: Flash hesapları açılınca ranked-backup büyük A/B (testbench/films/ORCA_RB, token_1112/ab/film_bench_base.py, sıra ORB_A1,B1,A2,B2; makbuz sayımı token_1112/ab/ab_say.py). Mini film: istek -%5, token -%4, FULL_PASS 14→11 [[ranked-backup-ab-1112]] [[flash-kapasite-1113]]
- 2026-11-15 Belgesel kalanlar: ikinci Pocket iscisi, foto havuzu azalinca ek sorgu (SearXNG kismi 15 Kas bitti: VDS'e tasindi)
- 2026-11-18 Hedef 30 dk (kullanici 11-18): belgesel kisa film ve LimitClock bolumu uctan uca <30 dk, kalite ayni; durum Kanallar/ortak_duzelt/dagitim/HEDEF_30DK.md
- 2026-11-19 Belgesel 30dk A/B yarım kaldı (11-19): yamalar testbench/doc_hiz_1118 (ef3439d + repo2 dalga2 + scripts_s1); B1c S3 -%50 tek ölçüm; A2/B2 tam film yok. Ayrıca S1 TTS bozuk cümlede (kadın sesine kayma) tüm S1'i düşürüyor, cümle başı yeniden üretim gerekli. doc_ab_1118 (harness+çıktılar, 12 GB) 11-19 disk temizliğinde kullanıcı onayıyla silindi; yeniden kurmak gerekir.
- 2026-11-19 SkullStudio run_episode adımları plan_v4.py/plan_v5.py + cutaways.py, cutaway_codegen.py, gen_fullbody.py, gen_newposes.py hâlâ doğrudan 9router'a istek atıyor (common.flash gemweb'e geçti, bunlar geçmedi; 11-19 /models 200 dönüyor ama 9router devri bitti). ZeroPulse oturumu gemweb.sor_json'a geçirmeli, testbench'te 1 bölüm plan adımıyla doğrulamalı.
- 2026-11-19 Kaynak planı ucuz adımları (11-19 süzgeçten geçti, beyin/ders/kaynak-plani-suzgec-1119): gemweb'e yalnız log X-Kanal/X-Sinif + kredi farkı jsonl (sunucu yeniden başlatılırken, gemweb oturumu yapar); ortak/kaynak.py havuz kilidi bekci.py opt-in; silmeyen disk_raporu
- 2026-11-19 2026-11-26: tarama/operator ajan seçilme sayısını say (11-19'da tarifler 'ÖNCE bunu seç' diye sertleşti; taban tarama 0, operator ~13/7 gün; beyin/ders/orkestrasyon-fikir-suzgec-1119)
