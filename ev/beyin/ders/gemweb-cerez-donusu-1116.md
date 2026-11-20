---
tur: ders
aciklama: gemweb: 5 hesap aynı anda UNAUTHENTICATED = çerez bitmedi; kota RPC jSf9Qc code 7 kütüphanede hesabı kilitliyor
kaynak: testbench/gemweb_1116/server.py; gemini_webapi client.py:503
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# gemweb-cerez-donusu-1116

16 Kas 13:02: 5 hesap aynı saniyede 0,0 sn'de UNAUTHENTICATED. Sebep: Firefox __Secure-1PSIDTS'i döndürünce sunucunun tuttuğu eski çerezle kota RPC'si (jSf9Qc, _fetch_quota/_fetch_usage_info) code 7 alıyor; gemini_webapi _parse_rpc_results bunu görünce account_status=UNAUTHENTICATED yapıyor, sonraki generate Google'a gitmeden düşüyor. Üretim çerezi aslında hâlâ geçerli. 5 hesap tek Firefox çerez setini paylaştığı için hepsi birlikte düşer. Belirti: panelde 5 saatlik/haftalık 'bilgi yok' önce gelir. Anlık çözüm: POST /yenile/<hesap>. Kalıcı: server.py istek sonrası account_status AVAILABLE değilse a.cli=None; UNAUTHENTICATED hatasında dinlendirmeden bir kez taze çerezle yeniden dene.
