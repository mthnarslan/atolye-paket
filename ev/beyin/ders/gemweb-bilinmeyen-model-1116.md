---
tur: ders
aciklama: gemweb: kayıtsız model adı (argon) 10 hesabı dinlenmeye sokuyordu; artık sunucu hesaba gitmeden 400 dönüyor
kaynak: testbench/gemweb_1116/server.py
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# gemweb-bilinmeyen-model-1116

16 Kas 17:59: tek istek gemini-4-argon -> kütüphane ValueError Unknown model name -> server.py bunu hesap hatası sayıp 10 hesabı sırayla 15 dk SOGUMA'ya aldı. Düzeltme server.py içinde: chat() model adını hesapların modeller listesine bakar, yoksa 400 + geçerli adlar; ValueError Unknown model -> BilinmeyenModel (400), hesap dinlenmez. Dinlenen hesapları açmak: POST /yenile/<ad> (bash döngüsünde python print çıktısındaki \r'yi tr -d ile sil).
