---
tur: ders
aciklama: Kaggle T4 Blender: Eevee GPU 10 sn 1080p30 = 218 sn (Cycles 608 sn), kalite Cycles'a yakin; EGL icin /usr/local/nvidia/lib64/libEGL_nvidia.so.0 vendor json'u yaz
kaynak: oturum 2026-11-08; oturum 2026-11-08; oturum 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# kaggle-blender-1108

Hesap metehankahraman, CLI token ~/.kaggle/access_token, 'kaggle quota' haftalik GPU 30 sa/TPU 20 sa (Cumartesi 00:00 UTC yenilenir). kernel-metadata enable_gpu+enable_internet; machine_shape vermezsen P100 -> 10+ dk QUEUED kaldi; 'NvidiaTeslaT4' aninda RUNNING. Blender 4.5.3 x64 indirme+kurulum 29 sn. T4 tek kare 1080p 128 sample: CUDA 23,3 sn, OPTIX 25,1 sn (ilk kare, cihaz hazirlik dahil; animasyonda kare basi daha dusuk olabilir, olculmedi), CPU 198 sn, Eevee 112 sn + EGL hatasi (headless Eevee GPU kullanmiyor). Gorsel dogru. Test dosyalari scratch kaggle_blender/. Coklu hesap Kaggle kurallarina aykiri (tum hesaplar kapanabilir).

## 2026-11-08 (claude)

EK 2026-11-08 animasyon: 300 kare 1080p30, Cycles OPTIX cihaz, 64 sample, denoiser OPENIMAGEDENOISE+denoising_use_gpu (OPTIX denoiser 'Failed to create OptiX denoiser' ile durur), use_persistent_data. Render 607,7 sn = 2,03 sn/kare, oturum 641 sn, kota 0,13->0,30 sa (0,17 sa). Haftalik 30 sa ile ~176 x 10 sn klip = ~29 dk Cycles video/hafta (bu basit sahnede). Eevee GPU headless'ta EGL hatasiyla CPU'ya dusuyor (112 sn/kare) - duzeltilmesi hizli yolun anahtari. Kullanici dakikalarca beklemeyi kabul etmiyor; hizli secenek Eevee GPU/Godot.

## 2026-11-08 (claude)

EK 2026-11-08 Eevee GPU: Kaggle'da Eevee GPU'ya baglanmasi icin apt libegl1 libopengl0 libglvnd0 + /usr/share/glvnd/egl_vendor.d/10_nvidia.json {ICD library_path:/usr/local/nvidia/lib64/libEGL_nvidia.so.0} (surucu 580.178). BLENDER_EEVEE_NEXT taa_render_samples=32 use_raytracing: 30 kare 73 sn (cogu shader derleme ~1 dk sabit), 300 kare 218 sn (~0,7 sn/kare dahil derleme). Cycles ayni sahne 608 sn -> Eevee 2,8x hizli, gorsel cok yakin. Oturum 323 sn ~0,09 sa kota. Background modda gpu.platform.* cagirma (SystemError). Kaggle esZamanli en fazla 2 batch GPU oturumu ('Maximum batch GPU session count of 2'). Videolar scratch kaggle_eevee_10sn.mp4/kaggle_cycles_10sn.mp4.
