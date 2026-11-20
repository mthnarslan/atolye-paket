---
tur: kaynak
aciklama: YouTube edit teknigi taramasi: 1019 video akis + 49 kanal/86 alt teknik kutuphanesi; yollar, yontem, ban uyarisi
kaynak: documentary_materials/.claude/DURUM.md §4; ytmarket_run/editscan
olusturma: 2026-11-04
guncel: 2026-11-04
yazan: claude
onay: 
etiket: edit,youtube,arastirma
---
# edit-teknik-kutuphanesi

YouTube edit/teknik taramasinin sonuclari (1 Kas 2026). Ham veri burada degil; yollar asagida.

- **Akis taramasi bitti (1 Kas 11:05):** 1019 video, 18 yeni alt teknik. Yayin: Ortak Atolye `/edit/akis/`. Kod `C:\Users\meteh\ytmarket_run\editscan\` (`flow.py`, `state.db`).
- **deep50 kutuphanesi:** 49 kanal, 15 kart, 86 alt teknik + imza listesi (`/edit/`). Is akisi: `scale.py pick|dl|beats|group` → `merge.py` (library.json) → `cands.py` → `subtech.py` (Flash) → `subpick.py` → `build_page50.py`.
- **Joseph/teach:** `/edit/` en ustte ayri bolum; `ytmarket_run/editscan/teach` (`teach.py dl|chunks`, `synth.py`, `page.py`), yeniden calistirilabilir.
- **Nasil tarandi:** `scan9.py`: yt_gate ile video basina 3 kesit 240p indir → 9router'a inline video → sil. 3 paralel indirme + 25 paralel 9router: 27 video 315 sn. 2000 video ≈ 6 sa.
- **UYARI:** bu yogun video taramasi 1 Kas'ta 30 Antigravity hesabindan 23'unun Google tarafindan kapatilmasina yol acti. Toplu video taramasini tekrarlama. Bkz. [[antigravity-tos-ban]], [[gemini-key-pool-block]].
- Kullanicinin istegi: tum turler (yuzu gorunen dahil), cok dilli; ortak (≥%30) / nadir (≤%5) / altin liste + ornek link&t=. Begeni olcutu: [[edit-reference-taste]].
- Kalanlar: Flash ile patlayan/tutmayan karsilastirmasi yazilmadi. Melezleme sayfasi `yt_study\site\melezleme.html` kullanici yorumu bekliyor.
