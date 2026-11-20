---
tur: ders
aciklama: Oracle A1 (ARM) Blender: resmi arm64 build yok; apt 3.0.1'de Cycles SIYAH (ham 0), Eevee xvfb+llvmpipe ile calisir 1080p ~62 sn/kare
kaynak: oturum 2026-11-08
olusturma: 2026-11-08
guncel: 2026-11-08
yazan: claude
onay: 
etiket: 
---
# a1-blender-1108

blender.org sadece linux-x64 veriyor (5.2'ye kadar). A1'e apt blender 3.0.1 kuruldu; colormanagement klasoru eksikti, x64 3.0.1 tarball'dan /usr/share/blender/datafiles/colormanagement kopyalandi (yine 'role data' uyarisi, zararsiz). Cycles CPU arm64'te tum pikseller 0 (EXR dahil) -> kullanilmaz. Calisan: xvfb-run -a -s '-screen 0 1920x1080x24' blender -b -P sahne.py; Eevee 1080p 62 sn/kare (llvmpipe yazilim GL), Workbench 2,9 sn/kare. 10 sn 30fps animasyon Eevee ~5 saat: sadece durgun kare/kisa/dusuk cozunurluk icin. Test betigi ~/bltest/. Kaggle (haftalik ucretsiz GPU) icin hesap+API anahtari yok, kullanici acmali.
