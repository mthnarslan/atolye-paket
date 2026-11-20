# Beyin — tum Claude oturumlarinin ortak hafizasi

Duz md klasoru (Obsidian ile acilir, git ile surumlenir). Her oturum basinda hook ozet basar; tamami okunmaz.

## Okuma (sorgu)
1. Hook'un bastigi indeks ozetine bak. Konu varsa `index.md` → ilgili sayfayi ac. Tum klasoru tarama.
2. Bilgi eskiyse (`guncel` > 60 gun) ya da kodla celisiyorsa: kodu/olcumu esas al, sayfayi duzelt.
3. Iyi bir cevap/arastirma cikti mi? Sayfa olarak geri kaydet (sorgu da birikir).

## Yazma (ekle) — her zaman `araclar/ekle.py` ile, elle degil
- Ne zaman: bir sorunu cozdun, kullanici bir kural/tercih soyledi, olcum yaptin, yeni arac/yol kurdun,
  baska oturumun bilmesi gereken bir sey ogrendin. "Sonra yazarim" yok: ogrendigin an yaz.
- `python C:\Users\meteh\beyin\araclar\ekle.py --tur <ben|ders|konu|kanal|kaynak> --ad <kisa-ad> --aciklama "<tek satir>" --metin "<icerik>" --kaynak "<yol/commit/link>"`
- Ayni ad varsa sayfaya tarihli bolum eklenir (cift sayfa acma; once index'te ara).
- Acik is: `ekle.py --acik "is"`, bitince `ekle.py --kapat "is"`.

## Turler
| tur | icerik |
|---|---|
| ben | kullanici: kim, tercihler, calisma bicimi, yasaklar |
| ders | cozulmus sorun / kural: belirti → kok sebep → cozum → nasil uygulanir |
| konu | sistem bilgisi: servis, boru hatti, mimari, olcum sonuclari |
| kanal | kanal basi ozet (ayrinti `Kanallar\<Kanal>\CLAUDE.md`'de) |
| kaynak | buyuk veri/arac/link isaretcisi (veri kopyalanmaz, yolu yazilir) |

## Sayfa kurallari
- `aciklama` en onemli alan: index'te gorunur, arama ondan yapilir. Somut yaz (ne, ne zaman lazim).
- Her iddia kaynakli: dosya yolu, commit, olcum, video linki. Bilinmeyen alani bos birak, uydurma.
- Sayilar olculmus olsun ve tarihli. Tahmin ise "tahmin" yaz.
- Baglanti: `[[sayfa-adi]]`. Iliskili sayfalari linkle.
- `onay` alanini sadece kullanici doldurur. Icerik degisince ekle.py onu bosaltir.
- YASAK: API anahtari, parola, token, kimlik/fatura bilgisi (ekle.py reddeder). Kod buraya girmez; kod repo'da.
- Hizli degisen veri (kota, fiyat, anlik durum) yazilmaz; nasil olculecegi yazilir.

## Gunluk ve bakim
- `gunluk/YYYY-MM-DD.md`: oturum ozetleri (yapildi / karar / acik / kalici bilgi adayi). `tara.py` otomatik yazar
  (her oturum basinda arka planda, Haiku ile, degisen oturum kayitlarindan). Ayni tarama projelerin auto-memory
  dosyalarini da `ders/konu/ben`'e aktarir.
- `lint.py`: kirik link, kaynaksiz/aciklamasiz sayfa, yetim sayfa, eski sayfa, olasi cift sayfa, gizli bilgi.
  Sadece rapor verir; duzeltmeyi oturum yapar.
- Karar anlarinda ikinci goz: karsi-tez rolunde Sonnet alt ajani (fikir.py GPT/9router bitti, 11-19; karar senin).
- Ise baslamadan once: `araclar/ara.py "konu kelimeleri" [--n 4]` ilgili ders/konu sayfalarinin aciklamasini ve en iyi 2 satirini basar
  (~0,3 sn, ~2 KB). Kelimelerin yarisi gecmeyen sayfa elenir. Sonra gerekiyorsa sayfanin tamamini ac.
