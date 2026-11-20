---
tur: ders
aciklama: 3D explainer benzetme: gercek 3D (Three.js) + hazir varliklar
kaynak: claude 2026-11-12; testbench/opensect_1112/c3d; testbench/opensect_1112/out/OPENSECT_D_gercek_model.mp4
olusturma: 2026-11-12
guncel: 2026-11-12
yazan: claude
onay: 
etiket: 
---
# opensect-3d-benzetme-1112

testbench/opensect_1112 (lib.py, run.py). Ana kare nano_banana_pro 48 sn, 2x upscale 16 sn (2752x1536), omni_flash 6 sn 1080p klip ~100-125 sn; 20 klip + 16 resim 3 es zamanli istekle 17 dk. Sahne baslangic kareleri ana kare reference_images ile uretilince tank ayni kaliyor. A (start_image, klibin son karesinden devam): 2. klipte kayma var (kesit kapaniyor, plakalar tanktan ucuyor, alakasiz desen). B (her klibe NBP 'Edit of the given image... change only' ile son kare, mode start_end_image, reference_images=[bas,son]): olay istenen yerde bitiyor, referansa daha yakin. yt-dlp icin --js-runtimes node --remote-components ejs:github sart (yoksa 'only images available').

## 2026-11-12 düzeltme (kullanıcı kararı)
Kullanıcı iki AI videoyu da reddetti: sahne devamlılığı tutmuyor, B (baş+son anahtar kare) A'dan da kötü. Yukarıdaki "B daha kontrollü" yargısı yalnız kontak föyüne bakılarak verilmişti, yanlış. 3D explainer için AI video zinciri kullanılmaz; gerçek 3D gerekir (Blender yasak → tarayıcıda Three.js, kare kare render: `testbench/opensect_1112/c3d`, süreklilik tam). Kullanıcı ayrıca "çizgi film gibi değil, tam gerçekçi" istiyor: elle kodlanan model oyun grafiği gibi kalıyor; gerçekçilik için hazır ayrıntılı model + PBR doku + HDRI gerekir (indirme kullanıcı onayı ister). Teslimden önce ek yerlerine gerçek karede bak.

## 2026-11-12 (claude)

11-12 ek: Poly Haven (CC0) girissiz API ile iner: api.polyhaven.com/files/<ad> -> HDRI + doku URL. Three r181 HDRLoader ile HDRI arka plan+isik tek adimda gercekci gok verdi (c3d/world.js, eski hali world_v1.js). Sketchfab model indirme giris ister (kullanici pane'de girmeli); en uygun aday T-72AV 42manako 7c1ee239 (87k yuz, ERA'li, CC-BY).

## 2026-11-12 (claude)

11-12 D surumu: Sketchfab T-72AV (42manako, CC-BY) + Poly Haven HDRI/zemin ile 66 sn 1080p30 render 3 paralel parcada ~80 sn/parca. Tank tum sahnelerde ayni (devamlilik tamam). Kalan yapaylik: elle yapilmis kisimlar (kahraman ERA kutusu duz renk, ic mekan/murettebat, duman tek leke, cim kalin ve soluk, palet donmuyor). Ders: hazir model disinda kalan her elle yapilmis parca gercekciligi dusurur; kesit icin ici olan model ya da dokulu parca gerekir.
