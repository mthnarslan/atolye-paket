---
tur: ders
aciklama: Alt ajan ölçümü 7 gün/14 oturum: ana oturum araç çağrılarının %74'ü kendi sıralı Read/Grep/Bash, Agent %1,6; kural GPT işçisine yönlendirdiği için paralel Claude ajanı frenleniyordu; GPT bitince SISTEM.md kuralı paralel Haiku/Sonnet'e çevrildi
kaynak: scratch-2026-11-08 arastirma/4_alt_ajan_olcum.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# alt-ajan-paralellik-1119

Ölçüm (11-19, scratch arastirma/4_olcum.py): 488 Agent çağrısı, açılış mesajlarının %29'u paralel (en çok 7), %81 arka planda. 15+ ardışık araç zinciri ~660 (üst sınır; bekleme olabilir); en sıralı: documentary_materials oturumları ve ortak sistem oturumu. ZeroPulse, Haber ve 2 Kanallar oturumu hiç ajan açmadı. Ajan kullanan ve kullanmayan oturumlarda ana bağlam ort. ~120k aynı (sıkıştırma 166k'da kırpıyor) → kazanç bağlam değil, hız ve döküm temizliği. Karar (kullanıcı 11-19, GPT bitti): SISTEM.md 'Alt ajan dağıtımı' satırı: bağımsız işler aynı mesajda paralel Haiku/Sonnet; sınır paylaşılan kaynak (okuma 8-10, gemweb/GPU/render 4); aynı dosyaya iki yazar yok.
