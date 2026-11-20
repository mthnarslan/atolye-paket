---
tur: ders
aciklama: Landmark klip kapisi hydrogen: low tek basina cok sert (temiz 4/10), low->high kapi kotu 8/10 temiz 6/10, kosu arasi oynama yuksek, parse fail retry sayilmali
kaynak: testbench/landmark/gemweb_test/kanit/SONUC.md
olusturma: 2026-11-16
guncel: 2026-11-16
yazan: claude
onay: 
etiket: 
---
# gemweb-landmark-kapi-1116

16 Kas, testbench/landmark/gemweb_test/gate_test.py, 10 gorsel x2 kosu, 20 istek, 0 HTTP hata. Kotu yakalama: low 9/10, low->high 8/10 (niagara c6 yuzlu karede high bir kez gecirdi). Temiz gecis: low 4/10, low->high 6/10. sthelens c1 still'de hydrogen dogru (istem 2 kisi, karede 3), eski Flash kacirmisti. 1/20 cevap '_965' (parse fail) -> retry say. 9/20 cevap json citli. Sure: low medyan 16,9 sn, high 24,8 sn; low fail olunca kapi ~40 sn. Prod oncesi 20+ gorsel A/B.
