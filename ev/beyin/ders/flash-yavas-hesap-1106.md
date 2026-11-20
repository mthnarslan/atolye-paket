---
tur: ders
aciklama: Flash zaman aşımı: bazı antigravity hesapları Google tarafında 'yavaş şerit' (aynı proxy'de 2,5 sn vs 15-80 sn); ölç, yavaşları kapat
kaynak: flash timeout oturumu 2026-11-06
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# flash-yavas-hesap-1106

2026-11-06: Flash istekleri istemcide (cf_common 120 sn sert sınır) zaman aşımına uğruyordu; 9router'da 240 sn'yi aşan istek 502 ve 4 denemede 969 sn. Kök sebep proxy değil (TLS 0,1 sn, generate_204 0,15 sn) ve yük değil (170semohhhh 4 paralelde 2,5 sn): hesap başına Google yavaş şeridi. 'OK' istemi medyanı: hızlı grup ~2,5 sn (joelarry4820, elifkaya7391, 170semohhhh, huseyinbulut2047, reyhanih.s1360, hangarechoes, metehankahraman099, bluewings5858), orta ejderha582 4, cagdasozturk.works 6,5, soylutarot 8; yavaş jl0083069 32, yokbrar 17, hamidnezamzade66 16, robbiegaddbengals 15, ozturkcagdas437 11. Kapatılan: jl0083069, robbiegaddbengals, ozturkcagdas437 (yavaş) + hshsjskcic (403 TOS ban ama aktifti). Pasiflerden 12'si ban (403), soumithkumarkothir kota; yokbrar/hamid çalışır ama yavaş, kapalı kaldı. Free-tier (paid=free-tier) 4 hesap (ejderha0758, jeremytate329, johnsrob459, themetehanofficial) haftalık kotayı bitirdi, 07-09 Kas açılır; aktif bırakıldı, 9router CACHE_BLOCK ile anında atlar. Pro hesaplar g1-pro-tier, kota ~%96. Sonuç probe par12: 12/12, p50 4-5 sn, max 7-8 sn (önce max 40). Yeniden ölçüm: testbench/router_check/agspeed.py ve aggen.py VDS'te /tmp'ye kopyala, /tmp/r.sqlite = DB kopyası, çıktıyı proxy maskeli bas. DB yedeği /root/data.sqlite.bak-1106-flash.
