---
tur: kaynak
aciklama: freellmapi anahtarli olcum 11-20
kaynak: testbench/freellmapi_test/fl_bench.py ciktisi 2026-11-20; testbench/freellmapi_test/keyli2.txt; testbench/freellmapi_test
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# freellmapi-ilk-olcum-1120

Kurulum testbench/freellmapi (npm run dev, server :3001, panel :5173). Saglayici anahtarlari kullanici panelde kendisi ekler (Claude anahtar girmez). 11-20 olcum, test betigi testbench/freellmapi_test/fl_bench.py (10 kontrollu gorev: json, sayma, siralama, carpim, log, ceviri, duygu, tarih, baslik, kod): kilo-auto 10/10 ort 1,6 sn maks 2,7; 4 paralel kopya 40/40 ort 1,5 sn. auto 8/10 ort 5,4 sn (tarih+baslik AtlasCloud'da yanlis). Tek rotali anahtarsiz modeller (gpt-oss-120b, llama-3.3-70b, qwen3.5-397b) 1-2 istekten sonra rate-limit. Kilo istemleri egitim icin loglar; kullanici 11-20 sorun yok dedi.

## 11-20 ikinci olcum: tum anahtarsiz modeller (testbench/freellmapi_test/{kilo,ovh,horde}.txt)
- Limitler (kaynak kod yorumlari): Kilo 200 istek/saat/IP (tum :free modeller ortak), OVH 2 istek/dk/IP/model, AI Horde gonullu kuyruk. freellmapi'nin kendi birlesik anahtar siniri 120 istek/dk (21 paralel testte takildi).
- Cevap verenlerde dogruluk: qwen2.5-vl-72b 9/9, qwen3.8-27b 9/9, nemotron-3-ultra-550b 8/8, nemotron-3-nano-omni-reasoning 8/8, gpt-oss-120b 8/9, gpt-oss-20b 8/9, kilo-auto 10/10 (ilk olcum).
- Zayif: qwen3.5-397b, qwen3.6-27b, qwen3.5-9b, nemotron-3.5-lightning (json/siralama/kod yanlis; 400 token sinirinda dusunme ciktisi olabilir), mistral-small 4/7. llama-3.3-70b ve north-mini-code hic cevap vermedi; AI Horde 5 modelin hepsi hemen cooldown, kullanilamaz.

## 11-20 ucuncu: gercek limit ve alt ajan uygunlugu
- Anonim Kilo ~110 istekte PROMOTION_MODEL_LIMIT_REACHED ("Sign up for free"), OVH ayni anda yanit vermez oldu: anahtarsiz havuz pratikte saatte ~100 istek, uretim yuku tasimaz. Kapasite icin saglayici anahtari sart.
- Isci araci Kanallar/ortak/ucuz_llm.py (tek/--json/--batch, model zinciri, hepsi duserse exit 1 -> Haiku). stdin yalniz prompt yoksa okunur (acik pipe'ta takiliyordu).
- Son 48 saatte 159 alt ajan dokumu: 158'i >=3 arac cagrisi (77'si 31+). Alt ajan isi neredeyse tamamen aracli; metin-gir-metin-al ucuz model dogrudan devralamaz. Devralma ancak araclari calistiran bir dongu (or. freellmapi'nin /v1/messages ucuna yonlendirilmis ayri claude -p) ile denenebilir, o da anahtarli kapasite ister.

## 2026-11-20 (claude)

Anahtarli 4. olcum (11-20): 10 gorev: xkiro mistral-large-2512 10/10 0.8s, mistral-medium-3.5 10/10, cohere command-a-plus 10/10, openrouter nemotron-3.5-super-vl:free 10/10, agnes-3.0-flash 9/10, command-a-03 9/10, google gemini-robotics-er-2 7/10 (rate limit). Calismayan: nvidia 401 (anahtar gecersiz, nvapi- ile yeniden yapistir), zhipu rate-limit/dusunce metni, google gemini flash 30-60sn/timeout, navy model yok. Panel 'healthy' = yalniz model listesi; gercek istek sart. ucuz_llm.py zinciri anahtarli modeller one alindi.

## 2026-11-20 (claude)

5. olcum: 30 paralel/60 istek 59 dogru 8.6 sn. freellmapi /v1/messages (Anthropic) var: Claude Code bedava modelle araclariyla kosuyor -> Kanallar/ortak/ucuz_ajan.py. Masaustu alt oturumda env tasinirsa 401 (host OAuth); env -i ile temiz ortam sart. mistral-large ve command-a-plus basit dosya gorevini 4-8 sn dogru cozdu; zor gorev olculmedi. NVIDIA anahtari enabled=0 yapildi (401).
