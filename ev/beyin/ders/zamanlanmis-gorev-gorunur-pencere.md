---
tur: ders
aciklama: Görev Zamanlayıcı cmd işi görünür pencere açıyor; kapatılınca 0xC000013A (^C) ile ölüyor, iş yarım kalıyor
kaynak: argor_tarama 2026-11-11
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# zamanlanmis-gorev-gorunur-pencere

ArGor_Tarama 10 Kas 09:00'da 0xC000013A ile öldü (log'da ^C), WhatsApp gitmedi. Çözüm: eylem conhost.exe --headless cmd.exe /c calistir.cmd (pencere yok) + günde birkaç tetikleyici (09/13/19 + oturum açılışı) + betikte 'bugün gönderildi' işareti (wp_son.txt) + hata olursa WhatsApp'a hata mesajı.
