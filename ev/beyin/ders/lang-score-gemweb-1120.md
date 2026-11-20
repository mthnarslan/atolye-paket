---
tur: ders
aciklama: ytmarket_run/bin/lang_score.py başlık alaka süzgeci 9router'dan gemweb'e taşındı; LANG_NICHES env ile niş eklenir; nişi 6 dilde ölçmek ~5400 YT Data birimi
kaynak: ytmarket_run/bin/lang_score.py
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# lang-score-gemweb-1120

11-20: _flash -> Kanallar/gemweb.sor_json (yedek lang_score.py.bak1120). VOICE_PRIOR de=1 (DF Arena geçilemiyor, almanca-tts-dfarena-1119). LANG_NICHES=<json> desc/queries/topics ile NICHES günceller. Tek niş 6 dil ~5400 birim; ~40 niş tümü 4-5 gün kota. Python string içinde \n yazarken heredoc/replace gerçek satır sonu üretip SyntaxError verdi, Edit ile düzeltildi.
