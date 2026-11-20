---
tur: ders
aciklama: codex exec arka planda stdin acik kalinca 'Reading additional input from stdin...' deyip sonsuza dek bekler
kaynak: testbench/wildyear_1110 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# codex-exec-stdin-takilma-1110

Bash run_in_background ile codex exec baslatinca stdin kapatilmazsa codex 'Reading additional input from stdin...' satirinda takilir, hic calismaz (wildyear_1110'da 14 dk bosa gitti). Cozum: her zaman 'codex exec ... < /dev/null'. Baslattiktan 20 sn sonra log'da 'user' satirindan sonra ilerleme var mi bak.
