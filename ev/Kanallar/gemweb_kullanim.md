# gemweb: 9router Flash yerine yerel Gemini web sunucusu (16 Kas)

**Adres:** `http://127.0.0.1:8790/v1`. OpenAI uyumlu, `api_key` herhangi bir metin olabilir. Panel: `http://127.0.0.1:8790/`, durum: `/durum`.
**Kod:** `testbench/gemweb_1116/server.py`. Sunucuyu "Otomasyonu iyileştirme (fork)" oturumu yönetir. **Yeniden başlatma, kapatma.** Takılırsa panelden "yeniden bağlan" de.

## Model seçimi (kullanıcı kararı)
- **11-19: aktif modeller yalnız `gemini-4-hydrogen` ve `gemini-neon`** (karbon kilitli, argon yok); başka ad 400 döner. Ad `gemini-` ile başlamazsa artık hydrogen'e düşer.
- **Varsayılan: `gemini-4-hydrogen` + `reasoning_effort: "low"`.** Önce bunu dene.
- Low geçmezse `reasoning_effort: "high"` dene (düşünme açık). Medium diye ayrı seviye yok: "high" dışındaki her değer low sayılır.
- `gemini-flash-lite` kullanma: kullanıcı istemiyor, görselde hata metni dönüyor.
- `gemini-pro` takılıyor, 180 sn zaman aşımına düşüyor.
- Model adı `gemini-` ile başlamazsa (örn. `ag/gemini-3.8-flash-low`) sunucu flash-lite'a düşer. Model adını mutlaka değiştir.

## İstek gövdesi
- Gövde OpenAI ile aynı: `messages`, `model`, `reasoning_effort`.
- Görsel: `{"type":"image_url","image_url":{"url":"data:image/png;base64,..."}}`. Tam boy PNG gönder; küçültmek hız kazandırmadı, kaliteyi düşürdü.
- Ses/video (18 Kas akşam düzeldi): `{"type":"input_audio","input_audio":{"data":"<base64>","format":"mp3"}}` (wav/m4a/ogg). Sunucu web'in yolunu izler: push yükleme (`?authuser=N`) → ProcessFile RPC → ~8 sn bekleme (`GEMWEB_AVBEKLE`) → mesaj. hydrogen+high, 38–78 sn/istek, timeout ≥300. Video aynı yoldan ama test edilmedi. Kapatma `GEMWEB_AV=0`. Örnek: `testbench/gemweb_1116/sestest.py` (`beyin/ders/gemweb-ses-video-yukleme-1118`).
- Yanıttaki `usage` her zaman 0 gelir. Harcamayı paneldeki "Kredi" sütunundan oku: hydrogen istek başına ~4 kredi.
- **Ortak istemci:** `import gemweb` (`Kanallar/gemweb.py`): çit soyma, görsel reddi (GemwebRet), çöp yanıtta yeniden deneme, model adı kontrolü, makine geneli 30 slot (sira sunucuda FIFO; 11-19). Kendi ayrıştırıcını yazma. Bilinmeyen model adı (ör. gemini-4-argon) 16 Kas’ta 10 hesabı 15 dk dinlenmeye soktu.
- 502 "bu isteği işleyemedi" = model bu işi yapamadı. Bunu "geçemedi" diye say.

## Kapasite ve kurallar
- 10 hesap var (u0–u4 + p0–p4; p'ler kullanıcının kendi TR SOCKS5 proxy'si arkasında). 11-19'dan beri sunucu bekleyenleri geliş sırasıyla (FIFO) dağıtır; her hesap aynı anda 2 istek alır (`GEMWEB_HESAP_PARALEL`, 1095 gelince o hesap 1'e iner, 20 başarıda geri çıkar: `GEMWEB_KAP_SERI`), hesap başına öğrenilen aralık bekler. `/durum` her hesapta `kap`/`aktif` gösterir. 60 ağır istek 10 paralelde ~125 sn, p90 21–33 sn. İstemci sunucu yeniden başlarken (bağlantı reddi) 5 dk'ya kadar bekler, deneme saymaz (11-19). Sunucuyu `testbench/gemweb_1116/nobetci.py` ile başlatırsan çöküşte kendini yeniden açar (log `bekci_log/gemweb_nobetci.log`). 16 Kas denemesinde 10 paralel isteğin 10'u doğru döndü, her biri ayrı hesaba gitti, toplam 19 sn sürdü. Birden çok kanal aynı anda test ediyorsa paylaş: kanal başına ≤4.
- **Kredi tavanı (11-19):** her hesap 5 saatte 2400 kredi (istek ~11-18) → 10 hesap ~2100 istek/5 saat, haftalık ~44k istek. Sunucu 5h kredisi 40'ın altına düşen hesabı reset'e kadar atlar, en çok kalanı önce seçer (`GEMWEB_KREDI_ALT`); `/durum` → `kredi_5s`. Büyük parti öncesi `/durum`'a bak. Takılan akış 45 sn sessizlikte kesilip başka hesapta denenir (`GEMWEB_WATCHDOG`), aynı hesaptaki diğer istek artık düşmez (`beyin/ders/gemweb-kredi-watchdog-1119`). Sunucu 11-19'dan beri nobetci.py altında.
- Tek istek ~14–20 sn sürer.
- Hata alan hesap 15 dk dinlenir. Hesap başı limit: 5 saatte 2400 kredi, haftada 48384 kredi.
- **Toplu tarama yok:** aynı istemi yüzlerce kez basma. 9router hesapları bu yüzden banlandı.
- Test başına **≤60 istek**.
- 9router proxy'lerini bu sunucuya bağlama.

- 11-19: 1095 hesap başı hız sınırı; sunucu hesap aralığını kendisi öğrenir, 45 sn'de cevap yoksa boş hesapta ikinci kol açar. Geçici Google hatası (1095/1013/zaman aşımı) hesabı yalnız 60 sn dinlendirir; istemci zaman aşımı 400 sn (kendi istemcin varsa ≥400 ver). Hata/süre kaydı `testbench/gemweb_1116/istek.jsonl`.

## Ölçülen
ZERO PULSE görsel hakem probu, 14 sayfa:

| Model | Yakalanan hata | Temiz sayfada yanlış alarm | Koşu süresi |
|---|---|---|---|
| hydrogen low | 9–10/10 (kaçırdığı yalnız `cutoff`) | 0–2/4 | 59–71 sn |
| eski Flash low | 10/10 | 1/4 | 45–50 sn |

Hydrogen low hakem için yeterli. Ayrıntı: `beyin/ders/gemweb-hakem-model-1116`.

## Her kanal oturumunun yapacağı
1. Kanalının Flash çağrılarını bul: planlama, sınıflama, hakem/QA, metin, ses analizi ne varsa. Çağrının nerede yapıldığını (dosya:satır) ve modelin nereden okunduğunu (env / json / sabit) not et.
2. **Prod koduna dokunma.** Test, kopya ya da sarmalayıcıyla yapılır: base_url'ü :8790'a çevir, modeli `gemini-4-hydrogen` yap, `reasoning_effort` ekle (örnek: `testbench/skull/judgeprobe/gw.py`).
3. Her çağrı türü için küçük bir test koş: ≥2 koşu, bilinen doğru cevapla ya da eski Flash çıktısıyla karşılaştır. Çıktı JSON parse oluyor mu, kalite tutuyor mu, istek başı süre ne? Sayıları ham dosyadan al.
4. Sonuç tablosu yaz: çağrı | hydrogen low | (gerekirse) high | eski Flash | süre | karar.
5. Prod'a geçiş kullanıcı onayıyla ve testbench A/B'sinden sonra olur. Öneri olarak yaz.
6. Bitince Belgesel oturumuna (`local_bebb0c99-18e8-4858-bfb7-fcc4b4910903`) SendMessage ile ≤10 satır sonuç gönder. Sonuçları `kanit/` dosya yolunu vererek yaz.
7. Kalıcı bulguyu `beyin/araclar/ekle.py --tur ders` ile ekle.
