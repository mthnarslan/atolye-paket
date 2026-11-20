---
tur: ders
aciklama: gemweb: hesap basi 5 saatte 2400 kredi (istek ~11-18) asil tavan; kutuphane watchdog'u takilan akista tum oturumu kapatip ayni hesaptaki ikinci istegi dusuruyordu
kaynak: testbench/gemweb_1116 server.py, istek.jsonl, gemweb_err.log; gemini_webapi client.py _generate ~1825-1880, close 352
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# gemweb-kredi-watchdog-1119

Olcum 11-19 (gemini_webapi 2.1.1, :8790).
KREDI: her hesapta current_5h=2400 ve weekly=48384 kredi. Hydrogen istegi ~10-18 kredi (ort ~11): hesap basi 5 saatte ~210 istek, 10 hesap ~2100 istek/5 saat; haftalik ~44k istek. Ogle 12:06'da 4 hesap (u3,u4,u0,p0) 5h penceresinin %80-90'ini bitirmisti. Kaynak: client.usage_info (current_5h/weekly remaining_credits, reset_at), _fetch_quota() her istekten sonra. Yama yama_kredi_1119.py: secim 5h kalan < GEMWEB_KREDI_ALT (40) olan hesabi reset_at'e kadar atlar, en cok kalani once secer; /durum kredi_5s.
WATCHDOG: kutuphane akis sessiz kalinca (dusunme yokken min(timeout, watchdog_timeout)=120 sn) self.close() cagirip TUM http oturumunu kapatiyor; ayni hesapta kap 2 ile ikinci istek varsa o da 0,5-1,2 sn'de 'HTTP Error 0' / 'connection lost' ile dusuyor. Gorsel+high yukte (GAIATRACE 57 istek 15 paralel) 18 istek 180 sn sunucu ZAMAN'inda TimeoutError aldi. Yama: watchdog_timeout=GEMWEB_WATCHDOG (45) ile takilma ~60 sn'de kesilir ve baska hesapta denenir; yama_close_1119.py hesapta baska aktif istek varken close'u atlar (takilan akis break ile zaten kapanir). Dusunen akista esik timeout (120) kalir: 180 sn timeout bazen yine olur.
Test (yalniz watchdog+kredi, close yamasi oncesi): 40 gorsel+high, 15 paralel: 40/40 ok, 182 sn, medyan 27, p90 69, max 137 (istemci yeniden denemesiyle). Sunucu ici: 5x1095, 3 watchdog kesimi ~60 sn, 2 'HTTP Error 0' (close yan etkisi), 3 timeout 180.

## Ek 12:38 - 180 sn sinirina ragmen 434 sn
GAIATRACE 2. test (40 gorsel+high, 15 paralel): 15 dk'da 20/40; TimeoutError'lar 286-434 sn surdu, tum hesaplarda kap 1'de kaldi. Sebep: py3.12 `asyncio.wait_for` iptal edilen kutuphane gorevinin toparlanma dongusunu bitirmesini bekliyor; hesap o sure mesgul. Cozum (yama_kes_1119.py): `_sinirli()` gorevi asyncio.wait ile sinirlar, sure dolunca cancel edip BEKLEMEZ (birim test: iptali 3 sn geciktiren gorevde 1,0 sn'de kesti). Timeout artik kap'i 1'e indirmez (yalniz 1095/1013/1100), KAP_SERI 20->8. Ayrica close yamasi: hesap mesgulken (aktif>1) hic kapatma (yetim gorevin close'u da). nobetci.py kill testi: 66 sn'de geri geldi.

## Ek 12:57 - ag kopmasi 15 dk dinlenme
GAIATRACE 3. test: 180 sn kesme tuttu (max 190,6), p90 145->53 sn, >120 sn ok 7->1; ama 15 dk'da 25/40. 12:44-12:46 makine agi koptu (DNSError, curl 35/55/56, 'while connecting'; hem u hem p hesaplarda). Bu hatalar GECICI degildi -> SOGUMA 900 sn: 5 hesap 13:00'e kadar oyun disi. Yama yama_ag_1119.py: AG deseni (ConnectionError|SSLError|DNSError|curl 6/7/28/35/52/55/56|while connecting|connection reset/closed) -> 30 sn dinlenme, aralik katlanmaz. Yeniden baslatma nobetciyle 118 sn.

## Ek 13:20 - test 4: timeout yamalardan degil
GAIATRACE test 4 (ag yamasi sonrasi): 57 satir, 30 ok, 22 timeout 180 sn, p90 148. istek.jsonl tum gun: timeout YALNIZ gorsel+high isteklerde; 10:00-11:50 arasi ~90 gorsel+high istekte 0 timeout, 11:50'den beri %30-50 (11:50 12:10 watchdog/kredi yamasindan once). Ayni hesapta eszamanli istek etkisi yok (tek basina %32, 1 ortusen %22); u/p (IP) farki yok (%31/%38); kredi etkisi zayif. Hedge yukte hic acilmiyor (bos hesap yok -> kol 2 = 0). Sebep buyuk olasilikla Gemini tarafi (gorsel+high yavaslamasi/akis kaybi). Siradaki aday: gorsel+high icin 120 sn kesim + yukte de hedge.

## Ek 13:45 - gorsel+high kesimi 120 sn (yama_gy_1119.py, GEMWEB_ZAMAN_GORSEL_YUKSEK)
Ayni 40 istek 15 paralel: 180 sn kesim 15 dk'da bitmedi (test 4); 120 sn: 40/40, 684 sn, sunucuda ok max 57 sn, 25 timeout; 75 sn: 39/40, 685 sn, 27 timeout + 14 x 1095 -> kazanc yok, 120 kaldi. Takilan istek bastan takiliyor (basarili isteklerin %92'si <60 sn). Hedge yukte acilmiyor; yeniden deneme zaten kuyrukta onde, ek kol yalniz yuk ekler.
