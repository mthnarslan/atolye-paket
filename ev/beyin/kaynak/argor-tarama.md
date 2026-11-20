---
tur: kaynak
aciklama: Ar.Gör. ilan taraması: tara.py RG+OCR+Flash, her gün 09:00, WhatsApp özeti CallMeBot
kaynak: oturum 2026-11-06; oturum 2026-11-06; oturum 2026-11-09
olusturma: 2026-11-06
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# argor-tarama

Kullanıcının kendi araştırma görevlisi (makine/termodinamik) ilan takibi. C:\Users\meteh\argor_tarama\tara.py: RG eskiilanlar/YYYY/MM/YYYYMMDD-4.htm dizininden üniversite/enstitü PDF'leri; metin pypdf, resim ilan (RG 'RESİM' basımı, ~yarısı) rapidocr ile; kadro tablosu okunamazsa 9router flash-low'a sayfa görselleri (stream:false şart, yoksa boş gövde). İlk 35 gün 162 ilan, önbellekli tekrar 16 sn. AkademikTR çapraz kontrolü 4/4 eşleşti (2026-11-06). Çıktı rapor.md, yeni ilan varsa Windows bildirimi.

## 2026-11-06 (claude)

Zamanlama: Windows görevi ArGor_Tarama, her gün 09:00, StartWhenAvailable (PC kapalıysa açılınca çalışır). calistir.cmd -> tara.py, çıktı gunluk.log + rapor.md, yeni ilanda toast. Elle: Start-ScheduledTask ArGor_Tarama.

## 2026-11-09 (claude)

WhatsApp: tara.py wp_gonder() her çalışmada CallMeBot ile günlük özet atar (aktif ilanlar + kalan gün, yeni olanlar PDF linkli). Ayar argor_tarama\wp.json (phone, apikey; anahtarı buraya yazma). Yeni ilanda ayrıca toast + rapor.md ekranda açılır. CallMeBot GET, ~550 karakter URL sorunsuz.
