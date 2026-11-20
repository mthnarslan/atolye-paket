---
tur: ders
aciklama: DOCUMENTARY_LOGO_CLEANUP=1: wildlife'da BBC disi kliplerde kenar/kose logo kabul (sonra clean_overlay temizler); orta yazi, abone grafigi, URL, satici/lisans yazisi yine FAIL
kaynak: GaiaTrace EP01 HOOK 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# logo-cleanup-flag-1108

runner.py NON_BBC_NOTE tanimindan hemen sonra env kapisi (commit edilmedi, 2026-11-08). Kopru bu env ile baslatilmali (Start-Process oncesi env set). wildlife profili zaten nonbbc_from_start ile tum YouTube kanallarini bastan aliyor; eskiden NON_BBC_NOTE sadece kucuk kose bug kabul ediyordu, precheck logo_rule FAIL veriyordu (EP01 HOOK'ta 8/9/12. cekimler yazi yuzunden reddedildi). Stok satici (Getty/Shutterstock/Alamy) _license_overlay_noted ile yine reddedilir; temizlenmez. 9:16 gomulu icerik: testbench/pantanal_1108/tools/portrait_gate.py (keskinlik orani + sabit simetrik sinir), son kesitte kapi.
