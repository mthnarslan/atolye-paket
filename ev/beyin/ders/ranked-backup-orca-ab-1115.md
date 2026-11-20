---
tur: ders
aciklama: ORCA_RB 60 cekimlik buyuk A/B: B1 %12 istek/%19 token az ama B2 Flash 503/timeout ile gecersiz; yeni film klasorune referans ses+voicefix gerekir
kaynak: 
olusturma: 2026-11-15
guncel: 2026-11-15
yazan: operator
onay: 
etiket: testbench,ranked-backup,ab
---
# ranked-backup-orca-ab-1115

15 Kas testbench token_1112/ab (orb_side.ps1, orb_sum.py, orb_backup.py). ORCA_RB: A1 567 istek/2.44M gercek token/72 repair Flash/50 PASS(44 FULL_PASS)/2946 sn; B1 497/1.98M/30 Flash/33 yedek kullanildi 15 PASS/49 PASS(39 FULL)/2635 sn; A2 640/2.83M/92/45 PASS(33 FULL)/2794 sn; B2 GECERSIZ: Flash TimeoutError, plan 26 cekim, stage3 FAIL, 6293 sn, preflight sonrasi 9router 503. Plan cekim sayisi kosudan kosuya 45-60 degisir: istek/cekim ile normalle. Kurulum dersleri: (1) testbench filmi stage1 icin referans ses ister: films/<F>/ref.wav + DOCUMENTARY_VOICE_ENGINE=pocket, DOCUMENTARY_VOICE_REF=voices/jeff/ref.wav, REMOTE_ASR, PINPOINT=0 kopru env. (2) reference_voice_match FAIL (kisa son cumle kadin sesine kayiyor): speed_1106/voicefix.py --apply sonra ikinci kez kayarsa voice_repair_state.json override metnini degistir+master tasi, stage1 tekrar. (3) Docker Desktop acilinca Dify/lobechat konteynerleri de kalkar, RAM 1.3 GB'ya iner: searxng disindakileri docker stop. (4) Cekim sonucu: result.json status PASS + review_mode FULL_PASS/PASS_WITH_LIMITS; ab_say durumu kok 03_materials degil film kokunde okuyunca bos kalir.
