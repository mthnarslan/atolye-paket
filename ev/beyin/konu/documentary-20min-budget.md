---
tur: konu
aciklama: Belgesel faz suresi butcesi (10-21 olcumu: indirme 405 sn, shot uretimi 427 sn, darbogaz gateway); guncel hedef <=15 dk; range indirme uygulandi
kaynak: auto-memory C--Users-meteh/memory/documentary-20min-budget.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Kural: klasor yolu verilir -> tum adimlar sure hedefi altinda teslim edilir; gercek zamanli olculur, olculmemis kazanc butceye yazilmaz. **Guncel hedef <=15 dk (bkz [[speed-target]]); asagidaki 20 dk olcumu tarihi (2026-10-21, 1223 sn).**
Faz sureleri (170 shot, 70 kaynak): 3a indirme 405 sn, 3d shot uretimi 427 sn (worker-sn 6139: model cagrilari %58, 3D render+kodlama+kesme %42; duvar suresi = worker-sn / 15 isci, darbogaz gateway'de), 1.4 denetim 74 sn, 3c plan 104 sn, 4 render 77 sn.
3a: indirilen 4,76 GB'nin yalniz %35,6'si kullaniliyor; range indirme (HTTP 206, 14 sn pencere 1,4 sn / 1,6 MB) artik uygulandi: [[documentary-range-download-architecture]]. Yeni faz eklerken once olc, sonra butceye koy. Ilgili: [[documentary-pipeline-project]], [[documentary-plan-phase-gateway-stall]], [[voice-stage1-audit-findings]].
