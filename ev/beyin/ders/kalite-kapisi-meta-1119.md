---
tur: ders
aciklama: Kalite kapısı: metin_denetle KANCA + yeni meta_denetle.py (başlık etiketi, linksiz açıklama, sabit 3 hashtag); 53 videoda biz/insan ayırıyor
kaynak: oturum 1b6742da dogrula_kapi.py
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# kalite-kapisi-meta-1119

11-19. Kanallar/ortak/metin_denetle.py: son 4 cümlede sonraki-bölüm kancası (en/es/pt/fr/de/tr). 'see you in the next one' kalıbı eklenince insan kanalında 3 yanlış alarm verdi, çıkarıldı. Kanallar/ortak/meta_denetle.py meta.json (title/description; yt-dlp info.json da olur) ya da --baslik/--aciklama; çıkış 0/1/2. Doğrulama testbench/benzerlik_1114/feats 53 video: KANCA biz 15/31 insan 0/22; HASHTAG3 22/31 vs 1/22; LINK yok 31/31 vs 6/22; ETIKET 1/31 (Wild Year 'HOOK SFX MUSIC WM') vs 0/22. metin_denetle hiçbir hatta çağrılmıyordu (SISTEM satırı arşive düşmüştü); SISTEM'e geri yazıldı. Hatlara bağlama (SkullStudio, LimitClock lc/pkg.py, belgesel yükleme) kanal oturumlarının işi.
