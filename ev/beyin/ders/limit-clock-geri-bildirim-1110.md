---
tur: ders
aciklama: LIMIT CLOCK EP03 geri bildirimi: maskot dudak senkronu kaymasi (LC.life T ofseti), SFX cok kisik, gercek kesit = gercek YouTube b-roll (AI foto degil)
kaynak: LimitClock oturumu 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# limit-clock-geri-bildirim-1110

Kullanici EP03'u reddetti: (1) maskot konusmuyor/az/hareketsiz - asil sebep LC.life tweenleri segment zaman cizelgesinin 0'ina konuyordu, sahne T'de basladigi icin agiz kayik/donuk; life(tl,p,dur,g0,T) ile duzeltildi, agiz 2 kat buyutuldu, grafik sahnelerin ~yarisina sag-alt kose maskotu (yururek girer, 1.6-2.6 sn'de poz degistirir, grafigi gosterir) eklendi; kod LimitClock/lc/kit/lc.js. (2) SFX duyulmuyor: kazanclar ~+7 dB, her yazi/sayi girisine boom/thud+stinger vurus, l3'e whoosh+thud, icerige gore anahtar kelime ambiyansi (kabin basinci -> boom+wind+alarm), lc/mix.py. (3) 'Gercek kesit' = GERCEK video goruntusu (YouTube b-roll), AI fotogercekci uretim DEGIL; cizimler (murekkep) kullanicinin hosuna gidiyor, kalsin. lc/realcut.py: Flash high sorgu -> ytsearch -> 7 sn pencere -> Flash goz (eslesme, yazi/logo, yakin yuz, kaza/kan, kesme, kalite>=3) -> soguk grade; bulunamazsa murekkep still'e doner.
