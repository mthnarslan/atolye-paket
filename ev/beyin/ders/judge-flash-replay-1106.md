---
tur: ders
aciklama: Hakem replay: precheck Flash-low %97 uyum (GPT 37 sn -> 6 sn), review Flash %70 uyum + %21-29 yanlis gecis -> review GPT'de kalir
kaynak: testbench/judge_flash_1106
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# judge-flash-replay-1106

2026-11-06 4 film kayitlarindan GPT hakem kararlarini Flash'a yeniden sorduk (GPT'ye istek yok). Precheck n=16: low %97, yanlis gecis 0/4 (zayif kanit), median 6,1 sn (GPT 37 sn). Review n=35: low %70 / high %67, yanlis gecis 3/14-4/14, yanlis ret %32-34; GPT median 91 sn. 26 Eki replay ile tutarli. Oneri: precheck Flash-low (io.py ~768, onay + mini film sonrasi), review GPT'de tam 4 esZamanli. Ayrinti testbench/judge_flash_1106/REPORT.md
