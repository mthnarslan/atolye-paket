# gemweb kanal görevi (16 Kas, eş zamanlı tur)

Kullanıcının isteği: "kendi flash işlerinde nasıl kullancaklarını anlasınlar ve hemen testlere başlasınlar ... bütün sohbetler öğrensin kullanmayı bide verimli kullansınlar". Sonra ek olarak: "anında gidip onlarda eş zamanlı baksın artık işe dönmenin vakti geldi".

9router Flash'ın yerine artık yerel Gemini web sunucusu var: http://127.0.0.1:8790/v1 (OpenAI uyumlu). Eski Flash kotası dolu, 503 dönüyor.
Önce `C:\Users\meteh\Kanallar\gemweb_kullanim.md`'yi oku, oradaki adımları kendi kanalın için uygula.

## Eş zamanlı tur kuralı
- Şu an 5 kanal aynı anda test ediyor ve 5 hesabı paylaşıyor.
- **En fazla 2 paralel istek, test başına en fazla 40 istek.** Kuyruk uzarsa süreyi bekleme olarak değil, istek süresi olarak ölç (yanıttaki `hesap` ve süreyi kaydet).
- Kısa tut: kanalın gerçekten kullandığı Flash çağrıları, çağrı türü başına 2 koşu. Sonra işine dön.

## Dersler (Dağ, Haber, Zero Pulse, Metin yazma)
- Model `gemini-4-hydrogen`, `reasoning_effort: "low"`. Low tutmazsa yalnız o çağrıda high dene.
- Yanıtlar çoğunlukla ```json fence'iyle gelir: parse etmeden önce temizle. Bozuk yanıt (ör. tek satır "_965") = yeniden deneme.
- Karar koşudan koşuya kayabilir: tutarlılığı yaz.
- Kıyası bilinen doğruyla yap (lint/validate, elle etiketlenmiş örnek). Hakem çağrısında temiz örnek de koy. Model "hata var" der ama etiketin "temiz" derse kareyi büyütüp kontrol et; Dağ'da ve Haber'de hatalı olan etiketti.
- Metin hakemi temiz metne fazla itiraz ediyor: tek başına karar verdirme, ilk tarama say.
- Görsel tam boy PNG. Sunucuya dokunma. Prod koduna dokunma: testi kopya ya da sarmalayıcıyla testbench altında yap (örnek `testbench/gemweb_engineered_1116`).

## Teslim
- Ana oturuma (Belgesel, `local_bebb0c99-18e8-4858-bfb7-fcc4b4910903`) SendMessage ile ≤10 satır gönder: çağrı | hydrogen low | high (denediysen) | bilinen doğru | süre | karar, ve kanit/ yolu.
- Prod'a geçiş önerisini yaz, uygulama: kullanıcı onayı + A/B gerekir.
- UNAUTHENTICATED ya da hesap hatası çıkarsa dur, ana oturuma yaz.
- Kalıcı bulguyu `beyin/araclar/ekle.py --tur ders` ile ekle.
