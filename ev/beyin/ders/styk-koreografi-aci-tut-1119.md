---
tur: ders
aciklama: Styk cop adam: aci araya-girmesi en kisa yoldan (wrap), poz gecisi once tut sonra 0.2 sn hizli; dusuk renkte zemine gore figur rengi
kaynak: Avenox_inceleme 11-19
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# styk-koreografi-aci-tut-1119

Avenox v4 geri bildirimi 'garip el hareketleri': Ak.sample ve mix acilari dogrusal karistiriyordu, -0.7->3.6 gibi farkta on kol 3+ rad firliyordu. Cozum wrap(d)=(d+pi)%2pi-pi. Ikinci sebep: 0.5-2 sn'lik poz araliklari tum sure boyunca yavasca morflaniyordu ('takili/anlamsiz'). Cozum: aralik >0.3 sn ise son 0.2 sn'ye kadar eski pozda tut, sonra hizli gec; idle anahtarlari lin=2 ile yumusak kalir. Kosu kolu salinimi ~1 rad/kare idi; run1/run2 kol acilari daraltildi, adim 0.095. Tepki zamanlamasi: darbe olayi (muhur oturmasi = t0+0.22) bitmeden figur savrulmasin. Ana karakter eklenince cop adamlar onun tarafindan (sag) cekilir. Dosyalar: Avenox_inceleme/kontrol/_styk_blok.py, araclar/stil_y.py.
