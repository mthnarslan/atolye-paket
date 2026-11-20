# Gün raporu: 25 Ekim 2026

Hedef: Blackout (teknoloji) ile TOPIC_2–9 (8 hayvan belgeseli) filmlerini teslim etmek.
Saat 19:55 itibarıyla **teslim edilen ZIP sayısı: 0**.

## 1. Neden bu kadar uzun sürdü

Üretimin kendisi yavaş değil:
- Blackout'ta 208 çekimin hepsi onaylandı.
- TOPIC_2 173 çekimin 172'sine, TOPIC_3 197 çekimin 195'ine ulaştı.

Sorun şu: tek bir çekim geçmeyince film hiç render edilmiyor. Ben de bu takılmaları geç fark ettim. Gün boyu bu yüzden üç tür kayıp yaşandı:

1. **Tek çekim filmi kilitliyor.** 200 çekimin 199'u hazır olsa bile render başlamıyor. Bugün kilit sebeplerinin her biri ayrı bir hataydı (bkz. 2. bölüm).
2. **Kuyruk vazgeçiyordu.** `batch_films.py`, stage 3 düşünce sadece bir kez yeniden deniyordu. Sonra "NOT delivered" yazıp sıradaki filme geçiyordu.
   - TOPIC_2 ve TOPIC_3 17:40'tan beri 1–2 çekim eksik halde duruyordu.
   - TOPIC_5, 6 ve 7 ilk 5 dakikada geçici servis hatalarıyla düştü ve hiç yeniden denenmedi.
3. **Ben fark etmedim.** Bekçi (supervisor) bir olay yakalayınca bildirim gönderip kapanıyor. 15:42'deki olaydan sonra onu yeniden kurmadım. 15:42–19:50 arası hiçbir uyarı gelmedi.

## 2. Sabahtan bu yana bulunan sorunlar ve çözümleri

| # | Sorun | Etkisi | Çözüm | Durum |
|---|---|---|---|---|
| 1 | Bilgisayar 03:13 ve 06:13'te uykuya geçti (prizdeyken 15 dk uyku ayarı) | Gece işleri durdu | Sen powercfg ile kapattın; kuyruklar artık "uyanık kal" isteği gönderiyor | Çözüldü |
| 2 | 11:55'te bilgisayar donma noktasına geldi (RAM) | Her şey yavaşladı | Docker/Dify durduruldu (searxng hariç), işçi sayısı azaltıldı, BBC indirmesi duraklatıldı | Çözüldü |
| 3 | Blackout'ta grid ön eleme çekim başına 16 sn ekliyordu | Yavaşlık | `DOCUMENTARY_GRID_PREFILTER=0` | Çözüldü |
| 4 | SearXNG kapalıydı, foto araması 0 sonuç döndü | Plan çıkmaza girdi | `ensure_searxng` aramadan önce SearXNG'yi otomatik başlatıyor | Çözüldü |
| 5 | G-Labs sağlık kontrolü yük altında zaman aşımına düşüyordu | ANIM ve manzara üretimi atlanıyordu | Bekleme süresi 20/40 sn yapıldı | Çözüldü |
| 6 | Diskte olmayan pencere dosyası aday olarak sunuluyordu | Çekimler düşüyordu | Dosyası olmayan aday sunulmuyor | Çözüldü |
| 7 | Blackout'ta 37 fotoğrafla plan uygulanamıyordu, film hedefleri settings.json'a yazılıyordu | Planlama döngüye girdi | Hedefler artık `film_settings.json` dosyasından okunuyor | Çözüldü |
| 8 | Kuyruk, bridge yeniden başlarken tüm denemelerini bir saniyede tüketti | Film boşa düştü | Bridge'in ayağa kalkması bekleniyor, denemeler arasında 20 sn bekleme var | Çözüldü |
| 9 | Kod değişikliği tüm önbelleği geçersiz kılıyordu | Her yeniden başlatmada film baştan üretiliyordu | Önbellek kapsamı daraltıldı: yorum ve docstring sayılmıyor, her adım sadece kendi koduna bağlı | Çözüldü |
| 10 | **Bozuk katalog kayıtları:** pencere dosyası başka saniyelerle yeniden indirilmiş, katalog eski saniyeleri gösteriyordu (Blackout'ta 348 kaydın 45'i) | Blackout render'da 4 kez düştü | Dosyası o saniyeleri taşımayan kayıt aday olarak sunulmuyor (70bf0a4) | Çözüldü |
| 11 | **Canlı GPT denetimi** onaylı çekimi geri aldı; yeni görüntü bulunamadı ve eskisinin üzerine yazılmıştı | 2 çekim çözümsüz kaldı | Onaylı görüntü yedekleniyor; yeni seçim geçemezse yedek geri konuyor (496f27e) | Çözüldü |
| 12 | **ANIM çekimleri:** erken üretici çekimi onaylıyordu, ana işçi aynı çekimi yeniden üretip onaylının üzerine başarısız sonucu yazıyordu | Blackout'ta 53/61/110/147 her denemede düştü | Erken üreticinin onayı korunuyor (f591308) | Çözüldü |
| 13 | **Kameraya konuşan kişi** kuralını sadece render adımı denetliyordu | Blackout render'ı 18 dk sonra durdu | Kural stage 3 teslim kontrolüne de eklendi; çekim render'dan önce yeniden seçiliyor | Çözüldü |
| 14 | BBC dışı kesitlerde her logo reddediliyordu | Havuz daralıyordu | Köşede BBC'ninki kadar küçük logo kabul ediliyor (df7fde3) | Çözüldü |
| 15 | Kuyruk stage 3'ü bir kez deniyordu; stage 1–2'deki geçici hataları hiç yeniden denemiyordu | TOPIC_2/3/5/6/7 yarım kaldı | Stage 1–2 en çok 3 kez, stage 3–4 en çok 5 kez deneniyor | Yeni kuyrukta etkin |
| 16 | Bekçi her olaydan sonra kapanıyor ve yeniden kurulmayı bekliyor | 4 saat uyarısız geçti | Yeniden kuruldu; aşağıdaki "kendi kendini kurtaran kuyruk" maddesiyle bağımlılık kalkacak | Kısmen |
| 17 | Arama israfı: yedek sorgu aynı sorguyu tekrar gönderiyordu (%44'ü 5'ten az sonuç); hayvan filmlerinde Commons ve Archive'a giden 630 istek boşa gitti | Az kaynak | 3 düzeltme planlandı (bkz. 3. bölüm) | Bekliyor |

## 3. Hazır bekleyen hızlandırmalar (henüz devrede değil)

Çalışan filmlerin kataloğu baştan kurulmasın diye birleştirmeyi bekletiyorum. Blackout, TOPIC_2 ve TOPIC_3 teslim edilince birleştirilecek.

1. Flash hata beklemesi 300 sn → 15–60 sn.
2. Plan çıkmaza girdiğinde boşa genişletme turu yapılmıyor (önceden 66 dk'lık döngü oluşuyordu).
3. BBC pencere kesimi: bozuk pencere tek başına atlanıyor, kesimler 6 paralel.
4. AI manzara: 90 sn sınırı; G-Labs 403 hatası gelirse o filmde bir daha denenmiyor.
5. Arama 7 dil → İngilizce + 1 dil; aynı sahne için tek arama; sonuç vermeyen cümle tekrar aranmıyor.
6. Çekim süresi 4 sn varsayılan; sadece kaynak yetmeyince en fazla 7 sn.
7. Komşu birleştirme turları sabit 3 yerine, ilerleme olduğu sürece en fazla 8 tur.
8. BBC öncelik değil: BBC dışı logosuz kesitler en baştan havuza giriyor.

## 4. Günde 3 film nasıl olur

Ölçülen kapasite yetiyor. İki hat paralel çalışırken bir filmin stage 3'ü 2,5–3,5 saat sürüyor. Bu, kesinti olmazsa **günde 4–6 film** demek. Bugün kaybedilen süre üretimden değil, kilitlenip beklemekten geldi. Hedefe ulaşmak için:

1. **Film hiçbir zaman tek çekim yüzünden kilitlenmemeli.** Bütün denemelerden sonra çözülemeyen çekim için:
   - teknoloji filminde otomatik MOTION grafiği,
   - hayvan filminde komşu çekimin uzatılması, olmazsa AI manzara.
   Render her durumda yapılacak.
2. **Kendi kendini kurtaran kuyruk.** Teslim edilemeyen filmler listenin sonunda otomatik olarak tekrar denenecek. Takılma, benim fark etmeme bağlı kalmayacak.
3. **Kuralların tek yerde denetlenmesi.** Render adımının denetlediği her kural (kaynak sınırı, kameraya konuşan kişi, logo) stage 3'te de denetlenecek. Böylece render sonunda sürpriz çıkmayacak.
4. **Yukarıdaki 8 hızlandırmanın birleştirilmesi.** En çok kazandıranlar: Flash beklemesi, tekrar eden aramaların kaldırılması, 4 sn çekim ve BBC önceliğinin kalkması (daha geniş havuz, daha az eksik çekim).
5. **Bekçi.** Her teslim veya teslim edilemedi satırı, her takılma ve her döngü bana bildirim olarak düşüyor. Her bildirimden sonra bekçiyi hemen yeniden kuruyorum; 15:42'de olduğu gibi kurulmadan kalmayacak.
