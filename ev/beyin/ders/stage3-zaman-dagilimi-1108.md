---
tur: ders
aciklama: 1 dk film asama 3 569 sn: ~436 sn kuyruk oncesi (library_windows archive.org kesimleri 114 sn bekletir, hook_prescan 84 + plan_review 62, ilk 120 sn olaysiz arama), cekim kuyrugu sadece 132 sn; GPT/render yuvalari darbogaz degil
kaynak: GaiaTrace EP01 HOOK alt ajan analizi 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# stage3-zaman-dagilimi-1108

events.jsonl'dan (bridge log'da asama zamani yok). library_windows: bbc_library cut_windows 19 pencereyi archive.org'dan akitarak NVENC keser, DOCUMENTARY_BBC_CUTS=4 kuresel yuva (bbc_library.py:534) -> 5 film paralelde ~5x uzar. Envanter/plan kutuphaneyi bekliyor (sources.py:3180 as_completed hepsini bekler); YouTube satirlariyla plan erken baslatilabilir (~80-110 sn kazanc). render_with_qc ort 20 sn, gpt_before_render codex 19-25 sn, kuyruk beklemesi <=1.2 sn: GPT_SLOTS artirmak fayda etmez. Ret sonrasi seri kuyruk ~85 sn (6 Flash precheck reddi + 50 sn tek kaynak aramasi). Env-only guvenli hiz dugmesi yok; BBC_CUTS 4->6 sadece tek filmde.
