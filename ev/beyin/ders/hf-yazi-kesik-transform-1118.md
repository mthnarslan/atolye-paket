---
tur: ders
aciklama: HyperFrames: CSS transform ile ortalanan yaziya GSAP scale/y verince transform ezilir, yazi kenardan tasar (02:08 yarim baslik); ortalamayi left:0;right:0;text-align:center ile yap, render oncesi hf_metin_qa.py kapisi zorunlu
kaynak: hf/wa1117/v2, hf/army/build_ep.py
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# hf-yazi-kesik-transform-1118

11-18 USA vs Russia v3 02:08: sol ustte buyuk TEST karti yarim cikti. Sebep: kart translate(-50%) ile ortalanmisti, GSAP fromTo scale/y tween'i transform'u yeniden yazinca translate silindi. Cozum: animasyonlu yazida CSS transform kullanma (left:0;right:0;text-align:center ya da sabit left), punch/zoom'u yalniz gorsel katmana (.pz>.cam) ver, yazi .ov katmaninda. Kapi: python C:/Users/meteh/Kanallar/hf_metin_qa.py <dir> (CUT/OVERLAP, cikis 1 = render yok); hf/army/make_ep.sh bunu render'dan once zorunlu kosar.
