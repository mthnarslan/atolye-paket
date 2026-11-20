---
tur: konu
aciklama: Ortak beyin nasil calisir: neden kuruldu, parcalar (ekle/tara/lint/baslat/ara), SessionStart ozeti, birlesik.json, sinirlar
kaynak: testbench/ytmem altyazilari; araclar/fikir.py ciktisi 4 Kas
olusturma: 2026-11-04
guncel: 2026-11-06
yazan: claude
onay: 
etiket: beyin,meta
---
# beyin-sistemi

Ortak hafiza sistemi (4 Kas 2026'da kuruldu). Kurallar: `C:\Users\meteh\beyin\README.md`.

- **Neden:** auto-memory klasor basina bolunuyordu; bir oturumun ogrendigini digeri gormuyordu.
- **Tasarim:** otomatik ozet kalici sayfaya yazmaz, eszamanli yazma kilidi + atomik yazma, tara.py tek kopya / 30 dk aralik, Haiku ozeti sadece gunluk'e. Bilincli olarak yok: vektor DB, mem0; kayit icin bloklayan hook yok [[no-blocking-hooks]].
- **Parcalar:** `ekle.py` yaz; `tara.py` auto-memory aktarimi + gunluk; `lint.py` rapor; `baslat.py` SessionStart hook'u; `fikir.py` GPT+Flash ikinci goz; `ara.py` konu arama; `birlesik.json` birlestirilen sayfa adlari (`""` = bilerek silindi, tara.py geri getirmez).
- **SessionStart ozeti:** once kanal/acik isler/kullanici, sonra en yeni 15 ders aciklamasiyla, gerisi yalniz adlariyla.
- **Bilinen sinirlar:** ~1000 sayfada index buyur, hook sadece ilgili bolumu basmali. Hizli degisen veri buraya yazilmaz.

Kanal disi isler: Ar.Gor. ilan taramasi [[argor-tarama]].
