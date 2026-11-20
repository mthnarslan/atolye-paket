---
tur: ders
aciklama: HyperFrames: 3 render paralel (-w 2, tarayici GPU) seri'den ~1.8x hizli; 5 bolum (~55 dk video) 72 dk'da bitti; bos RAM 1.2 GB'a iner
kaynak: hf/army speed log_P*, log_Q*, bekci_log/armyrender.log
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# hf-paralel-render-1118

20 sn testte: tek 39 sn, 2 paralel (-w3) 53 sn/40 sn video, 3 paralel (-w2) 64 sn/60 sn video, bos RAM min 1.2 GB (16 GB makine). Gercek: 3 x ~10.7 dk bolum ayni anda ~42 dk; kuyruk xargs -P 3 (hf/army/run_all.sh). Ayrica: bekci altinda 'cmd | grep -v X' kullanirsan grep pipe'ta tamponlar, ilerleme gorunmez -> grep --line-buffered.
