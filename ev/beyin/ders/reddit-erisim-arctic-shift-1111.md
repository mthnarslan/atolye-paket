---
tur: ders
aciklama: Reddit verisi: reddit.com JSON giris sayfasi/403, PullPush 526; Arctic Shift calisir ama aralikli 422 'Timeout' verir, isciler pes eder
kaynak: testbench/ai_metin_1111/is/reddit3, reddit4 (2026-11-11)
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# reddit-erisim-arctic-shift-1111

Bu makineden reddit.com/*.json giris HTML'i ya da 403 doner; api.pullpush.io 526. Arctic Shift (arctic-shift.photon-reddit.com/api/posts/search ve comments/search) calisir ama aralikli: ayni sorgu bir dakika 200 (2-6 sn), sonra 0,4 sn'de 422 {'error':'Timeout. Maybe slow down a bit'} + x-ratelimit-reset basligi. 200 donen bicimler: subreddit + 1 haftalik after/before (+ title=AI, limit kucuk), comments/search?link_id=t3_<id>, comments/search?subreddit=X&body=...&1 hafta. Tarihsiz ya da aylik + title sorgusu daha sik 422. Uc GPT iscisi (sikayet_reddit, reddit2, reddit3) 4-5 denemede pes edip FAIL dondu: bu isi isciye verme; sabirli sirali toplayici kullan: testbench/ai_metin_1111/denetim/reddit_topla.py (haftalik pencere, 7 sn ara, 422'de reset+5 sn bekler, kaldigi yerden surer). Yogun saatte hic veri gelmeyebilir; baska saatte yeniden dene.
