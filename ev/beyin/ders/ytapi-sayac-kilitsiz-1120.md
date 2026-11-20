---
tur: ders
aciklama: ytapi.py kota defteri kilitsiz oku-yaz + yutulan OSError: eşzamanlı süreçte 200 kaydın 5'i sayıldı; 11-20 kilit eklendi
kaynak: ytmarket_run/bin/ytapi.py (bak-1120sayac), kanal1120/yedek_1120.json
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: ortak
---
# ytapi-sayac-kilitsiz-1120

ytmarket_run/bin/ytapi.py _note() ytapi_usage.json'u kilitsiz oku-değiştir-yaz yapıyordu, os.replace hatası 'except OSError: pass' ile yutuluyordu ve json.load(open()) dosyayı açık bırakıyordu (Windows'ta replace düşer). Sonuç: yedek_1120 koşusu search yaptığı halde ytapi_birim=0 yazdı; 4 süreç x 50 testte eski kod 5/200 saydı. Düzeltme 11-20: O_EXCL kilit dosyası + replace yeniden deneme + hata yükseltme + with ile dosya kapatma; test 200/200. Ders: sert tavan dayandığı sayaç sessiz hata yutuyorsa tavan yoktur; tavan sayacını eşzamanlı yazma testiyle doğrula. Ayrıca ytapi.api KEY.txt'deki birden çok anahtarı döndürüyor (5 anahtar) — 'tek anahtar' kararıyla çelişir.
