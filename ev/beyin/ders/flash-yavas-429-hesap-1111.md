---
tur: ders
aciklama: 9router Flash kuyruk gecikmesi (16-20 sn) 429 haftalik kota hesaplarindan: 9router onlari deneyip bekliyor; aktiften cikarinca max 20->5 sn
kaynak: oturum 2026-11-11
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# flash-yavas-429-hesap-1111

11-11: flash-low PAR8 16 istekte 4'u 17-20 sn. Dogrudan hesap probe (VDS /tmp/agp3.py, hesap basi 3 istek): 200 donen 5 hesap 2-5 sn (yavas hesap yok), 5 hesap 429 haftalik kota (soumith, jeremytate329, johnsrob459, ejderha0758, themetehanofficial). 9router bunlara sira gelince 429 alip bekleyip baska hesaba geciyor = kuyruk. Cozum: 429 hesaplari isActive=0 (yedek autobak/data-before-disable-429-1111.sqlite), sonra p50 2,3 max 5,3. Kota ~14 Kas acilinca probe edip geri ac. Kural: Flash yavaslarsa once dogrudan probe, 429/yavas hesabi kapat.
