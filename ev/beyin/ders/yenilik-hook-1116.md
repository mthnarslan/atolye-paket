---
tur: ders
aciklama: Calisan oturumlar SISTEM.md/beyin degisikligini gormuyordu; UserPromptSubmit hook yenilik_bildir.py her mesajda farki 2-12 satir basar
kaynak: ~/.claude/hooks/yenilik_bildir.py
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: ortak,hook
---
# yenilik-hook-1116

Sorun (16 Kas): SISTEM.md yalniz oturum acilisi/sikistirmada yuklenir; beyin cekme usulu (ara.py), acilis ozeti son 8 baslik. Gunlerce acik kanal oturumlari yeni kurallari bilmiyordu; elle yenilikler_1116.md gonderildi. Cozum: ~/.claude/hooks/yenilik_bildir.py (settings.json UserPromptSubmit, timeout 5). Oturum basina durum ~/.claude/hooks/state/yenilik_<sid>.json; ilk mesajda yalniz taban, sonra SISTEM.md yeni satirlari (<=5) + beyin ders/ben/kanal ve Kanallar/*.md degisen dosyalar (<=6, aciklama satiriyla). Degisiklik yoksa cikti yok. 0,17 sn. Oturumlar arasi mesajda da tetikleniyor. Yedek settings.json.bak_yenilik.

Guncelleme (16 Kas): yalniz 'ortak' etiketli ders + ben/ kurali ayrintili duyurulur; etiketsiz ders tek satir sayi. Kanallar/pano.md (pano.py) bildirilmez. Kanal durumu pano.py ile tek satir.
