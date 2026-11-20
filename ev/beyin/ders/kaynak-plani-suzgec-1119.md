---
tur: ders
aciklama: Kaynak/kapasite fikirleri karşı-tez süzgeci (11-19): gemweb çöküşü yük değil Google takılması + aralık şişmesi + ağ doygunluğu; otomatik kalıcı silme reddedildi
kaynak: oturum 1b6742da arastirma/fikir_3_kaynak.md, anti_kaynak.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: 
---
# kaynak-plani-suzgec-1119

Opus danışman: görsel+high zaman aşımı hesapta ikinci istek olsa da olmasa da ~%31 → hesap eklemek/paralellik düşürmek çözmez. Sebepler: Google tarafı takılma (12-14 arası), sunucunun zaman aşımını 1095 sayması (yamalandı), torch/HF indirmesiyle ağ doygunluğu. Karşı-tez sayı denetimi: bazı yüzdeler şişik (high %84→%79,8; 224/273→224/305); kredi/istek 4 mü 11-18 mi belirsiz, tavan hesapları tahmin. GEÇER/ucuz: (1) gemweb'e yalnız log: X-Kanal/X-Sinif başlığı + kredi farkı jsonl'e (server.py hesaplıyor, yazmıyor) — öncelik/kanarya ölçüm gelene kadar yok; (2) ortak/kaynak.py havuz kilidi (kurulum, gpu_agir, yukleme) bekci.py'de opt-in, --pid yolu bozulmaz, kilit beklerken takıldı alarmı vermez; (3) silmeyen disk_raporu + preflight disk uyarısı eşiği. REDDET: otomatik kalıcı silme / sınıf listesine toplu onay (kullanıcı kuralı tekil onay; teslim.py Drive doğrulamıyor), sabit sayfa dosyası (sistem ayarı, kullanıcının). ŞARTLI: onarım tavanı/SigLIP ön eleme/Gh→Gl = hakemi gevşetme kuralı (kanıt+onay+judgeprobe); 32 GB RAM/SSD kullanıcı kararı. gpu_clean.lock ile gpu_tts.lock birbirini beklemiyor iddiası kanıtsız.
