---
tur: ders
aciklama: G-Labs: hesap basina proxy atanınca 10 paralel nano_banana_pro 10/10 basarili, 128 sn duvar, istekler 10 proxy'ye dagildi
kaynak: landmark oturumu 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# glabs-hesap-proxy-10-paralel-1106

2026-11-06: 25 hesabin hepsine Google Accounts tablosunda proxy atandi (flow_accounts.json'da proxy alani dolu). Test testbench/landmark/clips/ptest/par10.py: 10 esZamanli nano_banana_pro gorsel, 10/10 ok, istek basi 60-128 sn, duvar 128 sn. Log 'Proxy: <ip>' satirlari 10 farkli proxy gosterdi (once 'Proxy: None' idi). Auth proxy listesi yalnizca captcha tarayicisi icindir. Sonraki partide clips/lane.py LM_GLABS_WORKERS=10.
