---
tur: ders
aciklama: Styk cop adamlari 'anlamsiz hareket' bulundu: poz listesi yerine fizikli Aktor (hazirlik+parabol+takla+inis, kart/baslik ustu zemin, olaya bagli an)
kaynak: Avenox_inceleme/kontrol/_styk_blok.py
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# styk-aktor-koreografi-1118

Avenox v3'te Styk figurleri sabit poz degistiriyordu, kullanici 'anlamsiz' dedi. v4: kontrol/_styk_blok.py Ak sinifi; anahtar (t, acilar, x, zemin, yon, donus, dogrusal). jump_to(tl,...) iniş anina gore geriye hesaplar: comelme 0.16 sn + 30 fps yogun parabol + tuck + 2pi takla + squat inis; drop() ekran ustunden superkahraman inisi; kick/punch/knock (savrulma + sirt ustu)/getup/cheer/floaty. Zemin = ekrandaki baslik/hap/kart ust kenari, an = o ogenin belirdigi S. Virus rolu ayri renk figur tekmeyle ekrandan ucar. Cizim yine Styk sitesi (styk_sahne.py ACT -> json -> styk_cek.py). Hap merkezini x0+genislik/2 ile hesapla (ilk denemede 60 px kaymisti).
