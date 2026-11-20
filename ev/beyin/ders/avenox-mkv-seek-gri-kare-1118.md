---
tur: ders
aciklama: cv2 ile ham.mkv'de CAP_PROP_POS_FRAMES seek gri/bos kare verdi; hep ileri grab()+read, geri gidiste onbellek/yeniden ac
kaynak: Avenox_inceleme/araclar/tam.py
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: 
---
# avenox-mkv-seek-gri-kare-1118

Avenox tam video (araclar/tam.py Ham sinifi): kontrol karesinde kayit penceresi bos gri cikti; kaynak kare saglamdi, sorun mkv seek'in kare-dogru olmamasi. Cozum: seek yok, ileri grab() ile atla, son 90 kare onbellekte, daha geri gerekirse VideoCapture'u yeniden ac. Tam video 5494 kare bekci altinda ~10 dk.
