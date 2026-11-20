---
tur: ders
aciklama: 9router bitti: belgesel io.py + SkullStudio flash varsayilani gemweb; gemweb 'unreadable image file' yanitini OK donduruyordu -> io.py yeniden dener
kaynak: testbench/gemweb_gecis_1118, testbench/teslim_1118/qa_mini_gw2
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# gemweb-gecis-unreadable-1118

18 Kas kullanici: 9router devri bitti. Belgesel io.py (io_gemweb.patch) ve SkullStudio common.py/cutaways.py varsayilani gemweb (env =9router eski yol). Ilk gercek cagrida gemweb {'fit':false,'subject':'unreadable image file'} dondu ve OK sayildi -> iyi klip sessizce reddedilirdi. io.py'ye regex korumasi: gemweb modunda 'unreadable image/cannot open the image' -> ValueError -> yeniden dene. Tekrar: fit true 'snowy forest trees', 87 sn. preflight chk_flash artik gemweb /v1/models (kredi harcamaz). sfx_qa: gemweb 5 sn olay kliplerinde SFX duymuyor (2/2 bos, yerel eslesme 0.998), genel kesit 2/3; API anahtari yok -> golge mod.
