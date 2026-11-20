---
tur: ders
aciklama: Asama 3 secici istemi tum VIDEO katalogunu her cekimde gonderir: EP02'de cekim basi ~22-42k token, film Flash tokeninin ~%58'i
kaynak: testbench/ab_1109/film_cost.py, ovh.py
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# selector-prompt-katalog-1109

EP02 Taiga makbuz dokumu (21.5M Flash prompt token, 2702 istek): shots/flash.json secici 343 istek 7.6M + repair_#/flash.json 5.0M; storyboard 1.56M, grid_prefilter 1.19M(+0.97M repair), precheck 1.14M(+0.85M), inventory 0.88M. Ornek secici istemi (cekim 0040) 42006 prompt token, gorselsiz: 437 VIDEO satirinin hepsi. Satir icinde bos source_context, problems [], quality_tier (boyutla ayni) var. Tahmin: kompakt satir -%32, kompakt + ilk 40 aday (+pinpoint/sentence_search) -%94 istem. testbench/ab_1109/B runner: DOCUMENTARY_SELECT_COMPACT=1, DOCUMENTARY_SELECT_CAP=40 (A/B suruyor, prod'da yok). Ayrica 9router antigravity her istege ~2000 sabit prompt token ekliyor (dogrudan Gemini 'hi'=2 token); Google tarafi, 9router ayarlari (caveman/ponytail/customPrompt kapali) degil. Gorsel ~1070 token sabit.
