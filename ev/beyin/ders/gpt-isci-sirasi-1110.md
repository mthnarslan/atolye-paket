---
tur: ders
aciklama: Alt ajan sirasi GPT -> Flash -> Claude: Kanallar/gpt_isci.py; codex exec Windows'ta tam erisim gerekir, isci PASS'i kanitla kontrol edilir
kaynak: testbench/gpt_isci_test, testbench/darbogaz_1109/ACCEPTED.md
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# gpt-isci-sirasi-1110

Kanallar/gpt_isci.py tek|toplu: codex exec (ChatGPT girisi; sol=gpt-6.1-sol uygulama, astra=gpt-6-astra ikinci gorus, luna=gpt-6-luna buyuk veri), limit hatasinda Flash'a (9router ag/gemini-3.8-flash-high, saglayici -c ile verilir, codex config'de tanim yok; en fazla 2 paralel), o da limitteyse CLAUDE_GEREK. Windows tuzaklari: varsayilan sandbox read-only (komutlar 'blocked by policy'); workspace-write + windows.sandbox=elevated ayri kullanicida kosar, PATH'te python yok; bu yuzden -s danger-full-access + kural istemi (commit/silme/QA gevsetme yok). stdin DEVNULL. Kanit dosyalari UTF-16 yazilabiliyor -> istemde UTF-8. 11-10 testi: sol 22 oge dogru, Flash 37 satir dogru (2,6 dk), luna 32 dedi yanlis (Measure-Object -Line bos satirlari saymaz) ama PASS yazdi -> PASS beyandir, Claude sayiyi kanit/ ile kontrol eder. 11-09 darbogaz_1109: 13 PASS'in 6'si kabul, 2'si uydurma. Avenox videosu (r9JPDb2E6lI): buyuk model yonetir, GPT asker gibi ayrintili istemle; Gemini talimat takibinde zayif; Fable abonelikte Opus'un 2,5-4 kati limit.
