---
tur: ders
aciklama: Asama 3 kuyruk bitince merge_rounds -> _produce_shots -> footage.refresh tum kaynaklari yeniden parmak izler; 5 filmde EP04 icin ~44 dk; parti sirasinda kod degisikligi _production_code_signature'i canli degistirir
kaynak: GaiaTrace 1108 parti, py-spy dump
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# merge-rounds-footage-refresh-1108

EP04 (5 film paralel) queue_done 00:08, merge_rounds icindeki _produce_shots her cagrida footage.refresh(out, assets) calistiriyor: kosu sirasinda eklenen supplemental pencereler onbellekte yok, ffprobe/ffmpeg parmak izi isleri MemoryGate hafif kuyruguna diger 4 filmle giriyor; 00:08-00:52 sadece bu. Ardindan 13 komsu cekim yeniden uretiliyor. Hizlandirma fikri (parti sonrasi): refresh'i yalniz yeni pencerelere sinirla ya da supplemental pencereleri inerken footage.prefetch'e ver; birlesen komsularda refresh atla. Parti sirasinda prod koda dokunma: _production_code_signature diskten her cagrida okunur, dosya degisirse biten filmlerin asama 3'u yeniden kosar. scan_cache disk deposu sadece import'ta okunur, dis surecle isitma calisan kopruye yansimaz.
