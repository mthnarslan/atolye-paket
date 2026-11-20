---
tur: ders
aciklama: VDS 9router cx/gpt-6.2-sol codex: 12/16 kalite; 8 paralel 16 is 16/16 9r, 429 yok, ~124k token/is; gpt_isci ilk yol
kaynak: testbench/freellmapi_test/replay/run_codex62.log; testbench/gpt9r_1120, Kanallar/bekci_log/gpt9r_yuk.log
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: 
---
# gpt62-sol-9router-ajan-1120

11-20: 9router VDS :20128 cx/gpt-6.2-sol /v1/models'ta gorunmuyor, dogrudan cagrilinca calisiyor; /v1/messages da var. Basit istek 24 paralel 24/24, 6,4 sn. 8 gercek salt-okunur alt ajan gorevi: Claude Code kabugunda Bash'siz 8/16; codex exec -s read-only medium ile 12/16 (5 gorev orijinal kadar iyi), toplam 954k token (gorev basi ort 119k, 8,6k-198k), 2-6 dk/gorev, 4 paralelde 429 yok. Bedava modeller 5-6/16. Ders: GPT'yi kendi kabugunda (codex) kostur, Claude Code kabugunda zayif. Istem 'arac cagrisi yok' derse literal alip dosya okumuyor. 9router uzerinden ChatGPT kota yuzdesi okunamiyor (codex --json rate_limits yok). Ham: testbench/freellmapi_test/replay.

## 2026-11-20 (claude)

Yuk testi 11-20 12:42-12:53: gpt_isci toplu 16 is --paralel 8 effort medium, hepsi sol/9r (dusen 0), log ERROR'da 429/limit 0, toplam 1.98M token (ort 124k), is basi 2,7-7,8 dk; 2 FAIL gorev icerigi (yerel dosya yok). gpt_isci KURAL istemiyle t21 52 blogu da yapti (ucuz kabukta yapmamisti). gpt_isci.py artik ilk yol 9r (GPT_ISCI_9R=0 kapatir). Codex 'model metadata not found' uyarisi zararsiz gorundu. Tek hesabin 8 ustu ve 5 saatlik kota tavani olculmedi; 9router kota yuzdesi vermiyor.
