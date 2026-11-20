---
tur: ders
aciklama: gpt_isci: VDS OceanAPI'de gpt-6-luna yok (400 Model not found), isci sessizce ChatGPT aboneligine dusuyordu; luna artik VDS'te sol kosar, varsayilan effort low
kaynak: Kanallar/gpt_isci.py; sorun_tara/isci/*/codex_luna_oc.log
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# gpt-isci-luna-vds-400-1118

11-18: 12 isci model=luna ile baslatildi, VDS :8765 hepsine 400 'Model gpt-6-luna not found' dondu, gpt_isci.py rc!=0 gorunce ChatGPT aboneligine gecti (kota yedi). VDS /v1/models listesinde gpt-6.1-sol, gpt-6-sol, gpt-6-astra var, luna yok. Duzeltme: gpt_isci.py OC_YOK={'luna':'sol'} ve varsayilan effort low (kullanici kurali: sol low). Yeni model eklerken once VDS /v1/models listesine bak.
