---
tur: ders
aciklama: Ayni kanal icinde hit/flop kapaklari yerel gorsel olculer (renk, kontrast, yazi var/kelime/alan, odak, kucuk boy kontrast) AYIRMIYOR: AUC 0.46-0.54 (564 kapak, 72 kanal)
kaynak: gate_olc 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# kapak-gorsel-ozellik-gate-1118

testbench/kapak_puan/gate_olc.py + gate.json (oran>=2.5 yuksek / <=0.5 dusuk, ayni kanal ciftleri 1104). Hicbir ozellik 0.54'u gecmedi; yazi_kelime 0.457 (hitlerde ort 4.6 kelime, flopta 6.0 - az yazi hafif lehte ama zayif). LLM hakemleri de gecersizdi (kapak-mutlak-hakem-1118). Sonuc: kanal icinde tiklamayi kapak 'cilasi' degil KONU/baslik + kapakta gosterilen ozne belirliyor. Kapak isinde olcut: nisin hit kapaklarinin gorsel dilini (ozne, olcek, yazi var/yok) izle, konunun en merak uyandiran somut nesnesini net goster, uzun yazi koyma; cila metrigiyle aday secme. Haar/yuz cv2 derlemesinde yok (CascadeClassifier yok); rapidocr_onnxruntime calisiyor.
