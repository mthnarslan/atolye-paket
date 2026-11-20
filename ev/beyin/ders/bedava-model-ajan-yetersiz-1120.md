---
tur: ders
aciklama: Bedava modeller (mistral-large, command-a-plus) gercek Sonnet/Haiku ajan gorevlerini yapamiyor: 8 gorevde 5/16 ve 6/16
kaynak: testbench/freellmapi_test/replay
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# bedava-model-ajan-yetersiz-1120

11-20: 8 gercek salt-okunur alt ajan gorevi ucuz_ajan.py (Claude Code + freellmapi /v1/messages, araclar Glob/Read/Grep) ile replay. Mistral-large 5/16, command-a-plus 6/16 (2=orijinal kadar iyi). 4 kosu 600 sn zaman asimi; Cohere arac kullanmadan uyduruyor (30 kaydin hepsi null); olgu denetiminde yanlis alarm; yanlis dosyayi anlatma. Sonuc: Sonnet/Haiku yerine ajan olarak KULLANMA; yalniz ucuz_llm.py ile ciktisi kodla dogrulanan mekanik tek istek (sayma, JSON, siralama, kisa ceviri). Ham: testbench/freellmapi_test/replay.
