---
tur: ders
aciklama: Asama 3 gun sonu surunmesi: repair_allocation API zaman asiminda break ediyordu (8/8 blocked = timeout); pkg_1107 Flash tekrar + GPT timeout=FAIL gibi not
kaynak: testbench/pkg_1107/APPLY.md
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# allocation-repair-timeout-1107

EP02-05 1106'da 8 allocation_repair_blocked olayinin hepsi API zaman asimi: 6 Flash secici (allocation_semantics; o saatte FLASH_TO_GPT offload ile gpt-6-sol'a gidip 45-70 sn'de dusuyordu, 9aee2ff sonrasi Flash'ta 5-21 sn) + 2 GPT plan incelemesi (ReadTimeout 45-162 sn). Runner bloklaninca break ediyor, cekimler cozumsuz kaliyor, fullrun yeniden basliyor (EP04 ana kuyruk 1 sa, toplam 2,7 sa, 6 yeniden baslama). Prod'da GPT'nin FAIL karari zaten bloklamiyor; timeout FAIL'den sert davraniyordu. Duzeltme testbench/pkg_1107 (sadece planning.py, cekim hash'i disinda): Flash secici bir kez daha, GPT timeout -> allocation_review_fallback notu. Cevrimdisi replay testi tests/test_alloc_fallback.py (prod RAISE, yeni OK). Prod'a uygulama APPLY.md, parti bitince + kullanici onayi. Danismanlar (GPT, Flash, Argon) ortak oneri: siradaki darbogaz SELECTOR_NO_MATCH erken medya degisimi; ama fallback'ler %10 geciyor (film basi ~7 gercek goruntu), kalite riski -> A/B sart. Bar kapisi dusuk deger (23 retten 4'unu yakaladi, 12 PASS'i isaretledi).
