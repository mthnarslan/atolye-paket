---
tur: ders
aciklama: vidIQ/gemweb kredi tavanı ajana sonradan mesajla verilirse geç kalır; tavan betiğe başlangıçta sert sayaç olarak gömülmeli
kaynak: ytmarket_run/secrets/vidiq_ledger.tsv, kanal1120/dil/vidiq_kredi_plani.md
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: ortak
---
# vidiq-tavan-scriptte-1120

11-20: dil süzgeci ajanına önce 'bakiyenin %60'ına kadar tek koşu' izni verildi; kullanıcı 'tek seferde bitirme' deyince %20 tavanı mesajla gönderildi ama ajan arka plan koşusunu ancak ~10 dk sonra gördü: 388 çağrı / 1940 kredi (%39). Kural: vidIQ kullanan her koşu, başlangıçta betiğe yazılmış bir sert tavanla (env VIDIQ_BUDGET ya da sabit) başlar; ajan briefinde kredi tavanı başlangıç bakiyesinin ≤%20'si; ham ledger secrets/vidiq_ledger.tsv ile denetlenir. Mini önce, tam koşu ayrı onayla.
