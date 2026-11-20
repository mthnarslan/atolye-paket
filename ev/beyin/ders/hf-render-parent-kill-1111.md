---
tur: ders
aciklama: HyperFrames render'i sarmalayan bash kuyrugu oldurulurse render 'render_cancelled_parent_exited' ile iptal olur
kaynak: ZeroPulse/LimitClock logs/finish.log
olusturma: 2026-11-11
guncel: 2026-11-11
yazan: claude
onay: 
etiket: 
---
# hf-render-parent-kill-1111

LIMIT CLOCK 11-11: queue.sh'i kill edince icindeki finish.py -> npx hyperframes render 'Render cancelled: render_cancelled_parent_exited' verdi, 14 dk render bosa gitti. Kuyrugu degistirirken suren finish bitmeden bash'i oldurme; yeni kuyruga suren bolumu ekleme, bekle. Ayrica Windows'ta Path.write_text varsayilan cp1254: emoji iceren json'da UnicodeEncodeError -> her zaman encoding='utf8'.
