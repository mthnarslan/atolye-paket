---
tur: ders
aciklama: gemweb :8790 ses dosyasini dinliyor (18 Kas aksam): push ?authuser=N + ProcessFile RPC + 8 sn bekleme
kaynak: testbench/gemweb_1116 ses_dene.py, /tmp/sfxdene*.py; PR #179; testbench/gemweb_1116/server.py; github.com/HanaokaYuzu/Gemini-API/issues/374; oturum 238b861c, 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# gemweb-ses-video-yukleme-1118

11-18 olcum: eski yol (content-push, [[url],ad]) ile 11 ses istegi 10'u CANNOT (tek ses, 5 ses, ses+resim, hydrogen ve pro). Yalniz mime eklemek ve 15 sn beklemek ise yaramadi. Web arayuzunun resumable yolu (push.clients6.google.com/upload, x-goog-upload-protocol resumable) + [[url,4,None,'audio/mpeg'],ad] ile ses birebir dogru cozuldu (p0, 26 sn). Ama ayni anda prod :8790 ayni hesaplari kullanirken test sunucusu (:8791) cogu hesapta 'error code 1100' aldi, sonuc karisik: temiz olcum prod yeniden baslatilinca tek sunucuda yapilmali. Yama testbench/gemweb_1116/server.py (yedek server.py.bak-ses1118): ses/video resumable+mime, video_url/file parcasi, client() 90 sn sinirli, TimeoutError ve 1100 icin dinlenme 120 sn (eskisi 900). TimeoutError sebebi: 9-10 dosyali istekler 180 sn'yi asiyor, hesap 15 dk cezaya girip havuz 10'dan 4'e dusuyor. Ust kaynak: github.com/HanaokaYuzu/Gemini-API/pull/179 (birlesmedi). gemweb-ses-okumuyor-api-yedek-1118 notunu duzeltir.

## 2026-11-18 (claude)

18 Kas aksam: yama :8790'a alindi, temiz test 7 istek: hepsi CANNOT/timeout. Desen: /u/0 hesaplar (p0,u0) ok ama CANNOT; /u/1+ hesaplar ~95 sn sonra APIError 1100 (authuser.py yalniz INIT/GENERATE'i /u/N'e ceviriyor, push.clients6 yuklemesini degil; x-goog-authuser basligi eklendi, p1 yine 1100). Eski yol+mime p0'da 113 sn CANNOT. Sabahki 2 basari tekrar etmedi. Upstream master'da duzeltme yok; issue #374: web build 20261112 istek bicimini degistirdi. Gercek cozum: tarayicida ses yukleyen gercek istegi yakalayip bicimi kopyalamak. O zamana kadar ses/video icin kendi API anahtarlari (sfx_qa api_json yedegi). Timeout duzeltmesi (BAGLAN 90 sn, timeout/1100 cezasi 2 dk) canlida kaldi. Hesaplar saglikli: 10/10 PRO, abuse Clean, 5 saatlik kullanim %1-8, haftalik %0-13.

## 2026-11-18 (claude)

Web build 20261117 ses/video icin: (1) push.clients6.google.com/upload/ resumable yukleme, /u/N hesapta URL'ye ?authuser=N sart (yoksa dosya hesap 0'a duser, mesaj 1100 verir; x-goog-authuser basligi ise yaramadi). (2) POST .../BardFrontendService/ProcessFile f.req=[null,'[[[url,null,1,mime],ad,null x6,[0]],null,1,["en"]]'] -> uuid. (3) ~8 sn bekle (beklemesiz CANNOT). (4) dosya girdisi [[url,4(ses)/2(video,tahmin),null,mime,uuid],ad,null x6,[0]]. Eski StreamGenerate bu bicimle calisiyor; web kendisi artik WebChannel processSession kullaniyor. PCck7e sadece okundu RPC'si. Kod testbench/gemweb_1116/server.py _gen/_up yamalari, GEMWEB_AV varsayilan 1. Test: u0 ve p1 hydrogen high, s003_en.mp3 birebir; sunucu uzerinden 38 sn. Video test edilmedi.
