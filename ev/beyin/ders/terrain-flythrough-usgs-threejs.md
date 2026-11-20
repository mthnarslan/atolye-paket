---
tur: ders
aciklama: Gercek 3D arazi ucusu kendi makinemizde: USGS 3DEP DEM + ortofoto -> three.js -> Playwright kare kare -> ffmpeg; 1080p ~5-8 fps
kaynak: Dag oturumu 2026-11-06 St. Helens ornegi
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# terrain-flythrough-usgs-threejs

Yontem (testbench/dag1/terrain): DEM = elevation.nationalmap.gov 3DEPElevation ImageServer exportImage (F32 TIFF, EPSG:4326, PIL okur) -> .f32 grid (1025^2). Ortofoto = basemap.nationalmap.gov USGSImageryOnly MapServer export (JPG 4096). index.html: PlaneGeometry DEM ile yukseltilir, MeshStandardMaterial ortofoto, ACES, gradyan gok + Fog; spec.json kamera keyframe (km, x=dogu z=guney) + opsiyonel tel kafes 'RECONSTRUCTION' konisi; window.renderAt(t) deterministik. render.py: Playwright Chrome headless (varsayilan GPU, high-performance bayragi YOK) -> jpeg q93 pipe -> libx264 -threads 4. 5 cekim 40 sn 1080p ~10 dk. Krater kesiti icin dag N-S degil acik tarafa dik (E-W) profil al; St. Helens krateri kuzeye acik, N-S kesitte canak gorunmez. Ayrica faster_whisper av hatasi (metadata_errors) -> soundfile ile numpy ver; CUDA cublas64_12 yok -> device=cpu int8.
