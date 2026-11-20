---
tur: ders
aciklama: Ortak Atölye _middleware ranged() sadece video/ için 206 veriyordu; audio sarılamıyordu
kaynak: ortak-site cf4a5e7
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# ortak-site-audio-range-1113

Sesler sayfasında dalgaya tıklayınca ses sarılmıyordu (seekable.end=0). Sebep: functions/_middleware.js ranged() sadece content-type video/ için Range kesiyordu; mp3/wav tam dosya 200 dönüyordu. Çözüm: /^(video|audio)\// . Ayrıca <audio preload=none> loadedmetadata vermez, preload=auto kullan. Doğrulama: curl -r ile 206 + Content-Range, playwright ile wave tıklama 50% -> 92 sn/180.
