---
tur: ders
aciklama: ddgs zayif, GitHub API 60/saat, HN/SO anlamsiz, gemweb'te embedding yok
kaynak: 
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: arastirma
onay: 
etiket: 
---
# arastirma-araclari-islemeyenler-1119

19 Kas: (1) ddgs (DuckDuckGo kutuphanesi) 3 soruda 0/8/7 sonuc, 'No results found' hatasi; SearXNG VDS zaten DDG/Google/Brave toplar -> silindi, tekrar deneme. (2) api.github.com anahtarsiz 60 istek/saat ve IP basina paylasimli: oturum basinda 403 rate limit verdi (reset ~45 dk); arastir.py'de gh varyantlari hizli tuketir; gh/hf/hn/so anlamsal degil harfi harfine arar, tam sorgu 0 donerse 2'li kelime varyantlari (coklu()) dener; yine de HN/StackOverflow 'video clip' gibi sorgularda alakasiz (Comedy Central, phpmyadmin) -> SO varsayilandan cikarildi. (3) gemweb'te /embeddings yok: GPT-Researcher EMBEDDING=custom:hash + ortak/gemweb_adaptor.py (hash vektoru) gerekti; ilgi suzgeci kaba. GPT-Researcher pip install ilk denemede 500 sn timeout ile yarida kesildi (bagimlilik cozumu uzun, tam kurulum ~10 dk, 1,2 GB; torch yok). arXiv API paralel istekte 429 verir. (4) Semantic Scholar anahtarsiz 429, pullpush Reddit 521 (kapali): link_denetle Reddit'e pullpush ile baktigi icin Reddit linklerinde yanlis 'bulunamadi'. (5) bash'te 7,5 KB ustu komut hook'ta engelleniyor: betigi Write ile yaz.
