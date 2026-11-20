---
tur: konu
aciklama: Film hizlandirma guncel durum tablosu (olculen/suren deneyler); her hiz deneyi bitince guncelle
kaynak: testbench/speed_1106; testbench/speed_1106/PROFILE.md; testbench/speed_1106/FETCH.md; testbench/offload_1106/ORACLE_REPORT.md; testbench/speed_1106; scenefile/rtest_dist2.log; scenefile/rtest_gpu.log; testbench/speed_1106/render/SPEED_RENDER.md; scenefile/rtest_dist3.log; testbench/speed_1106/llm/BATCH_AB.md; testbench/speed_1106/llm/wait_ab.log; Kanallar/SISTEM.md Son degisiklikler 2026-11-07; documentary_materials git log; testbench/haber_1113/BULGULAR.md
olusturma: 2026-11-06
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# hiz-durumu

2026-11-06 durum. OLCULDU: mix NVENC 17x (sf.py varsayilan, --x264 eski) [[mix-nvenc-olcum-1106]]; Oracle proxy ile YouTube indirme calisiyor 1.5 MB/s/proxy, 4 paralel 5.4 [[sunucu-proxy-indirme-1106]]; Oracle ARM render ~9 sn/sn (PC 2.8) [[arm-hyperframes-chrome]]. SURUYOR (testbench/speed_1106): asama profili PROFILE.md, Pocket ses paralel/ikinci isci, yerel HF render ayari, GPT/Flash gecikme+toplu klip kontrolu, a1_fetch.py proxy on-indirme, Oracle paralel render. Hedef ~10 dk/film.

## 2026-11-06 (claude)

PROFIL (testbench/speed_1106/PROFILE.md, EP02-05 queue loglari): temiz yol seri ~4800 sn/film = asama1 ses+denetim ~1200, asama2 ~50, asama3 ~300 (son iyi kosu), asama4 QA ~170, sf plan ~350, sf render ~1250, sf mix x264 ~1450. NVENC ile ~58 dk tahmini. Gercek maliyet tekrarlarla 2-6 saat: asama3 tekrar/takilma toplam 9-21k sn, ses denetimi tekrarlari 3-9k sn -> en buyuk kazanc HATASIZ ilk kosu. Seri akis: sf plan asama4 QA ile paralel baslayabilir; drive.py'ye alt asama zaman satirlari eklenmeli.

## 2026-11-06 (claude)

INDIRME (FETCH.md): 9 EP02 kaynagi 652 MB: a1 proxy 158 sn (4.1 MB/s), ev sirali 79 sn, ev 4 paralel 29 sn (22.5 MB/s). Sonuc: indirmeyi Oracle'a tasima; ev hatti hizli. a1_fetch.py sadece ev IP/cerez engellenirse yedek. Indirme darbogaz degil.

## 2026-11-06 (claude)

RENDER DAGITIMI (ORACLE_REPORT.md): hiz video-sn/sn: PC 0.36 (2 paralel), a1 0.30 (3 ayri render -w 1; tek render -w 4 sadece 0.11, -w olceklenmiyor), VDS 0.12. ARM'de PRODUCER_FORCE_SCREENSHOT=true sart (yoksa 70 sn takilip ekran goruntusu moduna duser). ARM/x86 cikti ayni (SSIM 0.989). Yukleme 3.3 MB/s, parca 3-15 MB. Toplam 0.78 -> render ~28 dk -> ~14 dk tahmini. tools/remote_render.py; sf.py render artik is-calan kuyruk (PC+a1+vds, --local-only kapatir, uzak hata parcayi PC'ye geri verir, bos PC uzaktaki en eski parcayi spekulatif render eder).

## 2026-11-06 (claude)

SES (speed_1106/voice): Pocket sentezi 600 sn anlatim icin ~200 sn; tek sunucuda paralel istek fayda yok (kilit), POCKET_THREADS=2 en iyisi, 2. isci +%30 (~45 sn/film, +2.3 GB RAM) -> degmez. Asama1 ~1200 sn'nin cogu sentez degil DENETIM (Gemini transkripsiyon + tekrarlar); o kod .gemini/scripts'te (dokunma yasagi) -> kullanici onayi gerekir. LLM (speed_1106/llm): GPT plan 7 sn, Flash 140-200 sn -> yaris kalsin; klip kontrolu 8'li toplu 86 sn vs tekli 200+ sn, kararlar ayni -> cf_common toplu kontrol yaziliyor.

## 2026-11-06 (claude)

RENDER DAGITIM (commit 0297cb3): sf.py render artik yerel + a1 (3 slot -w1) + vds (1 slot) is-calma zamanlayicisi; CHUNK 55 sn; uzak parca yerel tahminden yavas kalacaksa yerel bosta spekulatif yeniden render eder, ilk gecerli dosya kazanir. 12 parca (288 sn video) testi: dagitik 386 sn vs sadece yerel 731 sn = 1,9x. Kapatmak icin --local-only. Hizlar RATE={local:0.22,a1:0.10,vds:0.12} video-sn/sn.

## 2026-11-06 (claude)

YEREL RENDER GPU: render_dir artik --gpu --no-browser-gpu (basarisizsa duz render). 12 parca sadece yerel 731 -> 364 sn (ajan olcumu %24, bu kosu yuk farkiyla 2x); SSIM gurultu tabaninda (0.9895 vs 0.990). RATE local 0.40. Dagitik + GPU birlikte bir sonraki filmde olculecek.

## 2026-11-06 (claude)

DAGITIK + GPU: 12 parca (288 sn video) 245 sn (yerel GPU tek basina 364, eski yerel 731) = eskiye gore 3x; 4 parca a1/vds'ye gitti. 10 dk film renderi tahmini ~8,5 dk (eskiden ~25 dk).

## 2026-11-06 (claude)

KLIP KONTROLU TOPLU (cf_common.check_rows batch): kod hazir ama varsayilan KAPALI (batch=False) cunku A/B olculemedi - gateway hastaydi ('say ok' 31-101 sn). testbench/speed_1106/llm/wait_ab.sh gateway <10 sn olunca A/B kosar; kararlar ayniysa varsayilan acilir.

## 2026-11-06 (claude)

KLIP KONTROLU TOPLU 2. deneme (12:24): ping 7 sn iken bile toplu yol 30 dk'da sonuc dosyasi uretmedi (timeout) -> 4'lu gorsel toplu istek gateway'de takiliyor. Kod cf_common'da kapali (batch=False), commit yok; acmadan once tek bir 4'lu istegin suresi elle olculmeli. Uretim hizi icin su an en buyuk kazanc render (3x) ve mix (17x) - ikisi commit'li.

## 2026-11-08 (claude)

11-07 OZET (Kasirga oturumu): pre_1107b EP02 42 dk, EP03 asama 3 2498 sn (baz ~73 dk). Prod'da: ANIM yarisi tur basina 2 aday 20ff5f2 (10 yuvada 372->270 sn) [[anim-race-1107]]; GPT incelemesi render oncesi kaynakta dc1d426 [[gpt-prerender-replay-1107]]; yan bant dedektoru 81b4a7d; uzun kategoriler kuyruk onune 5478439; asama 3 500'de bastan baslamiyor + medium merdiveni + ret hafizasi [[darbogaz-paketi-1107]]; Flash gizli dusunme kapandi: sf plan 1118->85 sn [[sfplan-flash-dusunme-1107]], factcheck 283->36 sn [[factcheck-flash-dusunme-1107]] (yeni Flash cagrisi reasoning_effort vermeli); Engineered sf render geciken uzak parcayi yerelde yeniden render eder 8389c28 [[remote-render-overdue-1107]], ikinci render seridi [[remote-render-lane-1107]]. Pinpoint artik varsayilan kapali (sources.py DOCUMENTARY_PINPOINT=0).

## 2026-11-13 (claude)

11-13 HABER DENETIMI: documentary_materials'a 11-08'den (a86e941) beri commit YOK; 9 Kas'ta kabul edilen stage-3 yamalarinin hicbiri prod'da degil. Tam tablo (23 BEKLIYOR, PROD, RED): testbench/haber_1113/BULGULAR.md. En onemli BEKLIYOR'lar:
1) SigLIP idle-release 600 s prod'da ZARARLI: 3 yeniden yuklemede +4442 MB private. Tek satir DOCUMENTARY_SIGLIP_IDLE_RELEASE_S=0 (parti disi kopru restart + kullanici karari). tb/darbogaz_1109/S6_bridge_memory/RESULT.md
2) S14 merged.diff (S2 restart dongusu 1154->1 s, S10 ret turu 90->5,8 s, S5 fill 1,77x, S8 EP06 848->369 s): S15 mini A/B ayirt edici degil, buyuk A/B bekliyor.
3) S4 baslik/portre kapisi: FP 3/100, ret 62/62 ama cekim basi +23,6 s ekler -> net etki bilinmiyor.
4) S13 window_index.ensure: face 69,2->4,6 s ama 0/20 PASS orneklemi + 2 hash testi FAIL -> pozitifli test gerek.
5) U_winidx ortak scale=320: pencere indeksi CPU -%19, 12/12 birebir; 2-3 donmali pencerede kontrol sonra uygula (scale_cuda -%79 ama 1 kesim kayip: onaysiz yok).
6) Selector COMPACT+CAP: prompt token -%39, 53/53 PASS ama F4+F5 ile karisik; temiz A/B >=3 kosu.
7) RANKED_BACKUP: token -%4, buyuk A/B ORCA_RB Flash acilinca.
8) Akisli ASR kodu prod'da (e7d74b5) ama Gaia'da calismamis gorunuyor; canli dogrulama.
9) clean_overlay toplu sizinti: EP03 81 is ~5->15,5 GB; N iste surec yenileme.
Ayrinti/kanit yollari tabloda.
