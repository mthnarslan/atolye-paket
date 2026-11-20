---
tur: ders
aciklama: LLM başlık hakemi temiz testte %73; kural %55, MiniLM+ridge %65, e5-large %58 — yerel model hakem olmaz
kaynak: ytmarket_run/reports/fremd1118/baslik/BASLIKLAR_FINAL.md; fremd1118/baslik/hakem_v1_test.json; fremd1118/baslik/hakem_v0_temiz.json, hakem_v1_temiz.json; fremd1118/baslik/emb/sonuc.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# baslik-hakem-dogrulama-1119

fremd1118/baslik: 20 Almanca KI/bilim kanalında 66 kanal içi çift (hit ≥3x flop). gemweb hydrogen high, çift başına iki sıra: 100/132 = %76 (dev 50/64, test 50/68; ikisi de Tem 2026 sonrası 71/96, ezber değil). Bu konu+ifadeyi birlikte ölçer; salt ifade seçiminde LLM şansa yakın (LOLA arXiv 2406.02611), varyant seçimini YouTube Test & Compare'e bırak. Özellik işaretleri (hit:flop): iki parçalı ':'/'–' 17:4, wir/du/uns 3:17, soru 8:18. Anti-tez astra başlıklarda 3 abartı buldu: Project Sid 1000 değil 500 ajan, 9000 sn (≈2,5 sa), din 20 rahiple tohumlandı. Ama 'test edilince farklı davranır' arXiv 2509.15541 nedensel kanıtla destekli; anti-tezi de kaynakla sına.

## 2026-11-19 (claude)

Ek: v1 (wir/du, soru, iki parçalı kuralları ipucu) test 58/68=%85, v0 50/68=%74; iki sırada tutarlı 32/34. Kurallar iki bölümün sayılarına bakılarak yazıldı, test temiz değil; temiz ölçü yeni kanallardan çift.

## 2026-11-19 (claude)

Temiz test (21 görülmemiş kanal, 55 çift, başka konular): v0 80/110=%73, kurallı v1 76/110=%69. Kural ipucu hakemi iyileştirmedi; sızıntılı testteki %85 yanıltıcıydı. Ders: kuralı gören veride ölçme, ayrı kanallarda ölç.

## 2026-11-19 (claude)

Temiz 55 çift (21 görülmemiş kanal): LLM v0 %73, kurallı v1 %69, kural modeli %55, MiniLM+ridge LOCO %65 (±%13), e5-large+ridge %58. GitHub/HF'de hazır Almanca başlık modeli yok; açık en iyi ifade modeli %63.6 (propensity-one). Karar: LLM v0 konu/başlık elemesi, ifade seçimi Test & Compare. Kod fremd1118/baslik/emb, rapor arastirma_repo.md.
