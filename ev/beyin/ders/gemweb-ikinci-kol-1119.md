---
tur: ders
aciklama: gemweb ikinci kol (hedge) yalniz 45. sn'de tek bakiyordu, yuk altinda hic acilmiyordu; artik uretim basindan 45 sn sonra 2 sn'de bir bos hesap arar, kol 2 sirada one gecer, ayni hesaba gitmez. Panel eski hatayi gostermez.
kaynak: testbench/gemweb_1116/yama_hedge_1119.py, /tmp/gwt/gorhigh10.log
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# gemweb-ikinci-kol-1119

11-19 17:22-17:49 olcum: 300 denemede 19 zaman asimi (180 sn), ikinci kol 1 kez acildi. Sebep: sor() 45. sn'de tek kez secim() bakiyordu + saat sira beklemesini de sayiyordu. Yama yama_hedge_1119.py (yedek server.py.bak-1119hedge): saat hesap uretmeye basladiginda (iz['bas']), 45 sn sonra her 2 sn bos hesap aranir (ilk kolun hesabi haric), kol 2 SIRA basina. Test gorhigh10 (40 gorsel+high, 15 paralel): 40/40, 160 denemede timeout 3 (%1,9; once %6), kol 2 12 kez acildi 9 kez kazandi. Toplam 509 sn (gorhigh8 313 sn) ama karsilastirma gecersiz: 10 hesabin 3'u 5 saatlik kotada <40 kredi (KREDI_ALT), 2'si <130, digeri oturumlarin yuku de vardi. Adil A/B kotalar sifirlaninca. Panel: basari son_hata'yi siler; /durum dinlenmeyen/baglanabilen hesapta 10 dk'dan eski hatayi gondermez (kullanici: guncel olmayan hata gorunmesin).
