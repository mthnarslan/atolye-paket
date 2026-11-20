---
tur: ders
aciklama: GPT gateway: sadece /v1/responses kuyruk+yeniden deneme alir; chat/completions ham gecis -> rastgele 502/503/504; '120 ,000' istegi her seferinde gecersiz yapar
kaynak: testbench/dub_1107 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# gpt-gateway-rota-1108

VDS :8765 gateway'de yalniz POST /v1/responses FIFO kuyruk + sinirsiz gecici yeniden deneme (429/5xx/timeout) aliyor; /v1/chat/completions dahil diger /v1/* ham gecis. Akissiz istek ~29/58 sn'de 504 yer. Dogru yol: /v1/responses + stream=True, SSE'den response.output_text.delta topla (ornek testbench/dub_1107/src/gpt_call.py). ASR'nin '120 ,000' yazimi istegi her seferinde 'The request is invalid' yapar: re.sub(r'(\d) ,(\d{3})', r'\1,\2', t). gpt-5.6-sol upstream'de gpt-6-sol'a esleniyor (ayri model degil). 'minimal' effort yok. gpt-6-astra cagirma (ucretsiz kredi yer).
