---
tur: konu
aciklama: 3c plan fazındaki 361 sn'nin kök nedeni gateway'in kendi yavaşlığı; deadline+hedge düzeltmesi ve ölçümü.
kaynak: auto-memory C--Users-meteh/memory/documentary-plan-phase-gateway-stall.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
3c plan fazi production'da 361 sn surdu (16+17 grup + 2 Codex review; yavas cagrilar 58-97 sn).

**Kok neden pipeline kuyrugu degil, gateway'in upstream gecikmesi:** her cagrida `queue_seconds ~ 0`, ucusta 2-12 istek (limit 15), ayni prompt bir grupta 7,8 sn digerinde 68,1 sn. Gateway 15 esze kadar bozulmadan calisir (medyan 6,4-6,8 sn, 20'de bozulma). `timeout=45` ise yaramadi: httpx her chunk'ta read-timeout'u yeniden baslatir, `timeout` ust sinir degil bekleme araligidir.
**Duzeltme (`planning.py::_planning_api()`):** `hedge_override=25`, `deadline = monotonic() + 25 + 45 = 70 sn` (deadline tek gercek sert sinir; hedge 25 sn'de ikinci istegi baslatip ilk yaniti kazandirir); Codex plan review ve 3D geometry cagrisina da deadline. Takilma enjekte eden sahte gateway'de duvar 45,6 -> 25,6 sn; saglikli gateway'de hedge hic atesmez (ek yuk sifir).
**How to apply:** bir API fazi yavassa once `queue_seconds` ve `active_channels`'a bak; sifirsa kuyruk degildir, `deadline` + `hedge` ekle ve sahte gateway ile dogrula. Ilgili: [[documentary-pipeline-project]], [[documentary-20min-budget]].
