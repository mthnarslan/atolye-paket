# gemini_webapi 2.1.1: görselli + extended_thinking akış takılması (araştırma 2026-11-19)

Yöntem: GitHub API (issues, search, pulls, releases, commits), PyPI listesi, README ham metni. Arama sayısı: HanaokaYuzu/Gemini-API için 9 anahtar kelime araması + ~12 issue/PR tek tek okundu; Nativu5/Gemini-FastAPI 1 arama + 2 PR; 4 repo arama sorgusu; zexadev/gemini-web2api-go release/issue/PR okundu; Reddit (api.pullpush.io) 4 sorgu denendi, sunucu HTTP 521 verdi; HN algolia 3 sorgu, ilgili yorum yok.

## 1. Kütüphane sürümü / changelog

- PyPI'daki son sürüm hâlâ 2.1.1 (pip index versions çıktısında en üstte 2.1.1, ardından 2.1.0, 2.0.0). Master'da 2.1.1'den sonra yalnız dependabot commit'leri var (son 2026-11-10); takılma düzeltmesi yok. Kaynak: https://github.com/HanaokaYuzu/Gemini-API/commits (2026-11-19 okundu).
- v2.1.1 (2026-08-27) yalnız çerez önbelleği düzeltmesi: https://github.com/HanaokaYuzu/Gemini-API/releases/tag/v2.1.1
- v2.1.0 (2026-08-15) extended thinking + watchdog'lu akış ekledi: https://github.com/HanaokaYuzu/Gemini-API/releases/tag/v2.1.0
- Zombi akış yeniden deneme mantığı v1.19.2 (2026-02-14): https://github.com/HanaokaYuzu/Gemini-API/pull/237

## 2. Doğrudan ilgili issue/PR (hepsi açık ve birleşmemiş, aksi belirtilmedikçe)

### PR #367 (2026-10-20, açık): ilk çıktıdan önce istek zaman aşımını kullan + yalnız-metadata takılmalarını yeniden dene
Bizim semptom: görsel ekli istem + muhakeme.
> "Pro reasoning and multimodal prompts (for example a product image attached to a text prompt) can legitimately take longer"

Önerilen değişiklik: ilk çıktıdan önce eşik = `timeout`, sonra sıkı watchdog; `@running` yeniden denemesi yalnız metin/düşünce/medya geldikten sonra engellensin (yalnız `[cid, rid]` taşıyan kare yeniden gönderilebilir). Birleşmedi; yerel yama olarak uygulanabilir.
https://github.com/HanaokaYuzu/Gemini-API/pull/367

### Issue #356 (2026-08-30, açık): paylaşılan istemci kapanınca eşzamanlı isteklerin ölmesi
Bizim "hesap başı 2 eşzamanlı, birinin close() çağrısı diğerini düşürüyor" bulgusunu doğrular.
> "A request-level failure or recovery should affect only that request."

v2.1.1'de de aynı olduğu yazılı. Çözüm yok (tasarım önerisi). https://github.com/HanaokaYuzu/Gemini-API/issues/356

### Issue #363 (2026-10-03, kapalı, yanlış alarm)
Yazar kendi `timeout=15` ayarının sebep olduğunu buldu. Kütüphane yazarının varsayılanlar açıklaması:
> "the default watchdog timeout is 120 seconds, while the default request timeout is 450 seconds"

Not: yerel kodda eşik `min(timeout, watchdog_timeout)`; `init(timeout=...)` ne verildiyse eşik o. https://github.com/HanaokaYuzu/Gemini-API/issues/363

### Issue #374 (2026-11-15, açık): Argon modeli 2026-11-12 web yapısından beri akışta takılıyor
Sürüm 2.1.1, Windows, çok PRO hesap; aynı hesapta diğer modeller normal.
> "Occasionally it succeeds after 70 s to 13 minutes."

Ardından Recovery polling zaman aşımı + "recovery timed out" hatası, bizim hata metniyle aynı. Tarayıcı artık StreamGenerate yerine WebChannel `processSession` kullanıyor. Extended thinking açık/kapalı fark etmemiş. Argon içindir; bizim model hydrogen ama zamanlama ve semptom benzer: Google tarafı protokol/yük değişikliği olasılığı. Çözüm yok. https://github.com/HanaokaYuzu/Gemini-API/issues/374

### Issue #294 / PR #301 / Issue #318 (Nisan 2026, açık): görsel üretiminde watchdog öldürmesi
- #294'te kullanıcı: "this happens at specific times" (2026-04-10), yani saate/yüke bağlı. https://github.com/HanaokaYuzu/Gemini-API/issues/294
- Yorumcu geçici çözümü: watchdog 120 -> 600, close_delay 450 -> 600; sahibi "seems like that was not the problem" demiş (işe yaramadı).
- PR #301 yalnız CLI varsayılanını değiştirir. https://github.com/HanaokaYuzu/Gemini-API/pull/301
- #318: görsel üretimi "queueing" + "No CID found to recover". https://github.com/HanaokaYuzu/Gemini-API/issues/318

### Issue #284 (2026-03-24, açık): ek dosyalı sohbetler aralıklı başarısız
> "A short warm-up turn in the same session can improve success rate to 40-60%"

Ek-ağırlıklı isteklerde upstream başarısı %10-20 bildirilmiş; ısınma turu hafifletme, çözüm değil. Bizim temporary tek çağrı modelinde uygulanabilirliği belirsiz. https://github.com/HanaokaYuzu/Gemini-API/issues/284

### PR #220 yorumu (2026-01-29, kütüphane yazarı): yoğun saat
> "limits large prompts and file attachments"

Yazarın cümlesi: yoğun saatlerde Google büyük istemleri ve dosya eklerini sınırlıyor. Bizim 11:50 sonrası yük artınca başlama gözlemini destekler; kütüphane aşamaz. https://github.com/HanaokaYuzu/Gemini-API/pull/220#issuecomment-3817819267

### Issue #235 (2026-02-11)
queueing döngüsü; yazar 1.19.1 ile akışı sıfırlayan watchdog ekledi. Tasarım: akış zombiyse bağlantıyı yenile + yeniden gönder. https://github.com/HanaokaYuzu/Gemini-API/issues/235

## 3. Başka sarmalayıcılar nasıl çözüyor

### Nativu5/Gemini-FastAPI (kütüphaneyi kullanan sunucu), PR #102 (2026-02-10)
`watchdog_timeout` parametresini bilerek ekledi, gerekçe:
> "boosting the chances of being redirected to an idle backend resource during peak hours"

Yani sessiz akışı kesip yeniden göndermek, yoğun saatte başka (boş) arka uca düşme şansı veriyor; ayrıca istek zaman aşımı 300 sn yapılmış. https://github.com/Nativu5/Gemini-FastAPI/pull/102

### zexadev/gemini-web2api-go (Go, 900+ yıldız, aktif): en ilgili kaynak
Aynı model (4 Hydrogen), aynı semptom, Issue #81 (2026-11-17):
> "首字节都在 2 秒内，说明上游已经开流；之后长时间没有任何内容。"

Ölçüm: 3 istek 144 sn / 196 sn / 254 sn (üçüncüsü çıktı 0, status 200). Kullanıcı önerisi:
> "「连续 N 秒没收到任何 chunk 就中断并重试」的空闲超时（例如 60 s）"

Yazarın yanıtı (2026-11-18): "建议设 60". v4.30.0 (2026-11-18) `stream_idle_timeout_sec` ekledi (akış açıldıktan sonra N sn chunk gelmezse keser ve koşulsuz yeniden dener; yalnız eski protokol StreamGenerate için geçerli, varsayılan kapalı, önerilen 60). Aynı issue'da 312 KB metin + 2 JPEG + stream için 4 kontrol deneyi 18-23 sn'de başarılı: sorun girdi boyutu değil, upstream'in ara sıra sessizleşmesi; üstelik hesap başı seri (`per_account_concurrency=1`) çalışırken de olmuş. Yani eşzamanlılık tek sebep değil.
- https://github.com/zexadev/gemini-web2api-go/issues/81
- https://github.com/zexadev/gemini-web2api-go/releases/tag/v4.30.0

Diğer ayarları (README, https://github.com/zexadev/gemini-web2api-go):
- `retry_on_timeout` açıklaması (重发多半还是超时): Toplam süre dolana kadar beklemek yerine erken kesmek mantıklı.
- `web_channel` (yeni protokol processSession): "老接口目前仍正常，老接口出问题时再打开" ve "扩展思考在新协议上暂时不生效". Yani extended thinking'i düşürür; bizim ihtiyaçla çelişir.
- Argon için ayrı çözüm PR #71 (2026-11-09): "不补的话付费号上请求会挂起没有回应" (tarayıcıyla aynı istek-gövdesi slotlarını doldurunca Ultra'da 15/15, doldurmayınca 9/27). Argon (mode 8) içindir; Hydrogen için kanıt yok. https://github.com/zexadev/gemini-web2api-go/pull/71

### Diğerleri
ntthanh2603/gemini-web-to-api: yalnız `GEMINI_MAX_RETRIES=3`, takılmaya özel çözüm yok. https://github.com/ntthanh2603/gemini-web-to-api . JS portu RahadyanRizqy/GAWA.JS 2025-09'dan beri bakımsız. gpt4free Gemini provider'ına bakılmadı (GitHub kod araması anahtarsız kapalı); "yok" değil "bakılmadı".

## 4. Reddit / HN
- Reddit (api.pullpush.io submission + comment): 4 sorgu denendi, HTTP 521, sonuç alınamadı.
- HN algolia: 3 sorguda ilgili takılma tartışması bulamadım.

## Sonuç
1. Yoğun saatte Google görselli/ek dosyalı istemleri kuyruğa alıyor ya da sessiz bırakıyor (kütüphane yazarı, #294, #284).
2. Takılan akış kendiliğinden toparlanmıyor (zexadev #81: 254 sn; #374: 70 sn-13 dk).
3. Kütüphane watchdog'u `client.close()` ile tüm oturumu kapatıyor (#356) ve aynı hesaptaki paralel isteği düşürüyor.
