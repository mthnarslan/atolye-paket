---
tur: ders
aciklama: Alt ajan orkestrasyonu süzgeci (11-19): 20 ajan varsayılan/A-B-C deneyi/dürtme hook'u reddedildi; tarama/operator tarifi sertleşti, 1 hafta sonra seçilme say
kaynak: oturum 1b6742da arastirma/fikir_1_orkestrasyon.md, anti_orkestrasyon.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# orkestrasyon-fikir-suzgec-1119

Opus danışman: 7 günde ana oturum 8.5k Bash / ~170 Agent; ajan açan mesajların %70'i tek ajan; 34 oturumun 20'si hiç açmamış; tarama ajanı 0 kez seçilmiş, operator ~13. Arka plan bash uyanmaları ana maliyetin ~%18'i. 20 ajan varsayılan: paylaşılan kilitler (gemweb/G-Labs/GPU/RAM) kaldırmaz, haftalık kullanım ~2,5-3x. Karşı-tez: dürtme hook'u REDDET (tuzak gemweb kuralı 954 tetikte %85 bastırıldı = dırdır), workflow/slash komut ve 3 kollu deney REDDET (kanıt yok, token), yeni 3 ajan yerine önce mevcut tarama/operator seçilsin. Yapılan: bekci_hatirlat.py ölü dosyaydı (mantık tuzak.py 60-62'de), ~/.claude/hooks/_arsiv'e taşındı; SISTEM ibaresi düzeltildi; tarama/operator description'larına 'ÖNCE bunu seç' eklendi. 2026-11-26 civarı: bu iki ajanın seçilme sayısını say (arastirma 4_olcum.py yöntemi, mtime değil kayıt zamanıyla süz).
