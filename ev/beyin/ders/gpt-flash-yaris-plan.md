---
tur: ders
aciklama: Plan istemi GPT'de 502/takilmada film 25 dk durdu; GPT + Flash-high paralel, ilk gecerli JSON kazanir; yavas Flash klip kontrolu kotu sayilmaz, yeniden sorulur
kaynak: Engineered scenefile 6 Kas
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# gpt-flash-yaris-plan

scenefile sf.py race(): GPT gpt-6-sol ve ag/gemini-3.8-flash-high aynı anda; ilk geçerli JSON alınır. EP02 planı 25 dk takılmadan 390 sn'ye indi. Haber ağırlıklı görüntüde (EP03: 50 klipten 33'ü yazılı) klipsiz kalan sahneler temiz klibin başka bir bölümünü (>=90 sn ara) yeniden kullanır, safe_rect yazıyı dışarıda bırakan 16:9 pencere keser.


**Yavas Flash klip kontrolu:** 12 paralel Flash gorsel kontrolde zaman asimina dusen klipler kotu sayilip EP05'te 22 iyi klip gereksiz degisiyordu. sf.py: zaman asimi olan kontrol rnd<3 ise pending'e girer, sonraki turda yeniden sorulur; ancak sonra bad. scenefile render'i hf_ffmpeg_shim ile (HF_X264_THREADS=4), mix -threads 4.
