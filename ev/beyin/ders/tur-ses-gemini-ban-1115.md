---
tur: ders
aciklama: 11-15 13:41-13:52: 9router antigravity hesapları toplu TOS 403; sabah 15 sağlam -> 2 (ejderha0758, johnsrob459) + 3 kota
kaynak: testbench/tur_dil_1115 kosA/B/C.log, VDS agall.py 11-15 14:10
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: claude
onay: 
etiket: 
---
# tur-ses-gemini-ban-1115

tur_dil_1115 ses toplama işi gün boyu 110 Gemini (ag/gemini-3.8-flash-high) ses hakem çağrısı yaptı (her çağrı 6-8 x 30 sn mp3, ~4 dk ses), 3 kos x 3 hücre paralel. Son başarılı 13:41, 13:52'den sonra hepsi 403 'service disabled ... Terms of Service'. VDS /tmp/agall.py: metehankahraman077/099, ejderha582, hamidnezamzade66, yokbrar dahil sabahki sağlamlar kapandı. Aynı saatte diğer oturumun film koşusu da Flash kullanıyordu; tek sebep kesin değil ama yoğun paralel ses yükü 1 Kas toplu taramasıyla aynı desen. Kural: 9router'a yoğun ses/video hakem yükü verme; paralel hücre sayısını 1-2'de tut ya da kendi tek API anahtarıyla az hacimde yap. Hata 'choices' KeyError olarak görünür; kos.py 3 denemede {} döndürüp adayları boşa harcar -> ilk 403'te dur.
