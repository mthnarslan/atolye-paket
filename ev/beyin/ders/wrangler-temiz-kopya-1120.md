---
tur: ders
aciklama: ortak-site deploy'u calisan agactan degil commit'li temiz kopyadan gonder
kaynak: Bulucu deploy 61576360, ortak-site ca0499d
olusturma: 2026-11-20
guncel: 2026-11-20
yazan: claude
onay: 
etiket: ortak
---
# wrangler-temiz-kopya-1120

wrangler pages deploy public, calisma agacindaki tum public'i gonderir: baska oturumun commit edilmemis dosyalari (11-20: public/index.html, nasil/metin, silinmis dub-*) canliya gider. Cozum: git worktree add <tmp> HEAD (ya da git archive HEAD public | tar -x -C tmp) ve deploy'u o klasorden yap, sonra worktree'yi kaldir.
