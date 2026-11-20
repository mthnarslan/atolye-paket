---
tur: ders
aciklama: bekci altinda komut ciktisini dosyaya yonlendirme: bekci 'sessiz' sanip cikar, hyperframes parent_exited ile %99'da iptal olur
kaynak: hf/wa1117/v2/render.log
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# bekci-yonlendirme-iptal-1118

11-18 v4 render: render_v4.sh ciktiyi render.log'a yonlendirdi, bekci kendi logunu 12 dk sessiz gordu, TAKILDI deyip cikti; hyperframes 'render_cancelled_parent_exited' ile %99'da (715 sn emek) iptal oldu. Kural: bekci -- komut altinda ciktiyi yonlendirme (stdout'a birak) ya da --log <dosya> ver. bekci cikinca alt sureci oldurmese de hyperframes parent'i izliyor.
