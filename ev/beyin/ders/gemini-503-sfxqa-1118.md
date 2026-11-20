---
tur: ders
aciklama: sfx_qa: Gemini API 503 high demand (3.5/3.6/3.8 flash hepsi) -> 'JSON donmedi' hatasi; 12 deneme artan beklemeli tekrar eklendi, bolumleri sirayla dinlet
kaynak: Kanallar/sfx_qa.py api_json
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# gemini-503-sfxqa-1118

11-18 aksam Grenzakten 04-06 SFX QA paralel kosunca tum Gemini cagrilari 503 'model is currently experiencing high demand' dondu; sfx_qa hata listesine 'Gemini API JSON donmedi' yazip cikis 2 verdi (kotu bulgu yok). Kapi gevsetilmedi: api_json'a 12 deneme, min(60,10n) sn bekleme eklendi; bolumler sirayla kosuluyor. gemini-3.6-pro 404 (yok).
