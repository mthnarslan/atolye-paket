---
tur: ders
aciklama: bekci.py ... | tail ile başlatılan render, bekçi RAM uyarısıyla çıkınca pipe kapanıp ölüyor; uzun render'ı Start-Process + log dosyasıyla başlat, bekçiyi --pid/--log ile bağla
kaynak: isaac2 v2 A/B render
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# bekci-pipe-render-olumu-1113

13 Kas isaac2: 'bekci.py -- npx render ... | tail' arka planda. Bekçi boş RAM düşünce 'iş hala çalışıyor' deyip çıktı; pipe kapandı ve render %74'te sessizce öldü, çıktı yok. Çözüm: render'ı PowerShell Start-Process -RedirectStandardOutput log ile bağımsız başlat, sonra bekci.py --log <log> --pid <pid>. Pipe'a bağlı uzun iş başlatma.
