---
tur: konu
aciklama: YouTube bot-block fix in production (2026-10-27) - global gate, shared caches, Firefox cookies via user env var; remaining risks
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/youtube-gate.md
olusturma: 2026-10-27
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Production yt_gate.py (9db9116 ve sonrasi): jeton kovasi TUM sureclerde ortak, `%LOCALAPPDATA%\documentary_materials\yt_cache\bucket.json` (prod + test koprusu tek butce paylasir), global backoff `backoff.json`, `yt_cache.py` (search/probe/window onbellegi); istek -%50 olculdu. Kullanici env `DOCUMENTARY_YT_COOKIES_BROWSER=firefox` (setx; 2500 istek/sa, olmadan 600/sa); kopruler env'i almak icin yeniden baslatilmali. bgutil PO sunucusu otomatik acilir.

**Why:** iki 4-film testi "Sign in to confirm you're not a bot" tetikledi; kalici cozum testlerde de gecerli olmali.
**How to apply:** gate'i atlayan kopru calistirma. Acik riskler: Firefox cerez suresi/rotasyonu (ayri profil onerilir), hesap isaretlenmesi, yt-dlp guncel tutma. Test duzeni tuzaklari: film klasorune `03_materials_*` kopyasi birakma (yerel varlik sanilip 1200 Flash grubu -> router timeout); girdisi cikti kokunde olan filmler `_voice_output`'a yazar ve tek teslim zip adini paylasir. Ilgili: [[post-delivery-test-plan]].
