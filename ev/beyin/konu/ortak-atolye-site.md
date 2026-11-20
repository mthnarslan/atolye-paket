---
tur: konu
aciklama: Ortak Atolye sitesi: yigin, deploy komutu, ISP SNI engeli + Vercel proxy, tasarim kurallari/layout_qa, gunun videosu adimlari, 25 MiB -> HLS
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/ortak-atolye-site.md
olusturma: 2026-10-31
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Ortak Atolye (2026-10-29): https://ortak-atolye.vercel.app. Kod `C:\Users\meteh\ortak-site` (git). Cloudflare Pages `ortak-atolye` + D1; deploy `npx wrangler pages deploy public --project-name ortak-atolye --branch main`. Turk ISP'leri `*.pages.dev` ve `*.workers.dev`'i SNI ile engelliyor, bu yuzden `vercel-proxy/` (Vercel rewrite) onde duruyor. Erisim middleware + SITE_KEYS; anahtarlar ve WRITE_TOKEN yalniz `C:\Users\meteh\Kanallar\ortak-site-anahtarlar.txt` icinde (repo disi). Oturumlar kart eklemek icin `tools/post_update.py` kullanir. Canli site anahtar arkasinda, Claude acamaz: kullanici kontrol eder.

**Tasarim (10-31, kullanici sectigi):** acik krem #f4efe3, turuncu #fc5424 (Belgesel), sari #ffc83d (ZERO PULSE), mavi #9db4ff (Ortak), 2px murekkep cerceve + sert golge, Bricolage Grotesque; ana sayfa = banner + sol film + sag liste; ortak sticky header (yeni sayfaya kopyala). Kurallar: yalniz grid/flex (absolute metin yok), eyebrow etiket/emoji ikon yok, transform/opacity hareketi, reduced-motion. Yayindan once `tools/layout_qa.js` 320/390/768/1024/1440'ta calistir ve ekran goruntusune bak (tarayici paneli animasyonda geride kalir, durumu DOM'dan dogrula). Ders: redesign oncesi ekran goruntulu secenek goster, kullanici secsin. Ilgili: [[explain-with-animated-page]].

**Gunun videosu:** HyperFrames projesi `C:\Users\meteh\hf\a<gun>` (kisa yol: Windows uzun yol render'i bozdu). `tools/lines_src.json` -> `python tools/tts.py` (kelime zamanlari) -> `python tools/build.py` (sahneler kelimelere sabit) -> `npx hyperframes check` -> render -> web kopyasi CRF 25 `ortak-site/public/v/` + `v/videos.json` basina giris (site yalniz `videos.json[0]`'i gosterir; mp4 git'te degil). Anlatim: her maddeyi ne -> test -> degisiklik -> sonuc diye, jargonsuz; ses karisimi icin SFX konusma altinda kisilir. Render 6 dk film ~13 dk; yayindan once kareleri kontrol et (eksik CSS sinifi SVG grid'i bozdu).
**25 MiB siniri:** Pages dosya basina 25 MiB; ~6 dk ustu filmler HLS (`ffmpeg -c copy -f hls -hls_time 6` -> `public/v/<gun>/index.m3u8`, segmentler gitignore). Asset sunucusu Range'i yok sayiyordu; `_middleware.js` artik 206 doner (ortak-site 72f448a).
