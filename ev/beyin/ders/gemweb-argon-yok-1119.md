---
tur: ders
aciklama: gemweb 10 hesabin Gemini menusunde Argon yok (Google'in sundugu liste: Otomatik/4 Hydrogen/4 Neon/4 Karbon); tarayici panelindeki hesapta 4 Argon var
kaynak: testbench/gemweb_1116/server.py /durum + gemini.google.com model menusu
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# gemweb-argon-yok-1119

19 Kas: sunucu model adlarini hesabin GET_USER_STATUS listesinden aliyor (gemini_webapi 2.1.1, hardcode yok). 10 gemweb hesabinin hepsi ayni 4 modeli donuyor: Otomatik, 4 Hydrogen (Gunluk isler), 4 Neon (Deeper analysis), 4 Karbon (Code & complex work, kilitsiz). Tarayici panelindeki Gemini hesabi farkli menu goruyor: 3.5 Flash-Lite, 4 Hydrogen, 3.1 Pro, 4 Argon (Kod ve analiz), 4 Karbon (kilitli). Yani Argon hesap/deney koluna bagli, sunucu hatasi degil. gemweb'de Argon yerine gemini-neon ya da gemini-karbon denenebilir; Argon'un model id'sini zorla gondermek hesaplari riske atar, yapilmadi.
