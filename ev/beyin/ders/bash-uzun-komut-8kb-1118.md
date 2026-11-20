---
tur: ders
aciklama: Bash araci: 7,5 KB ustu komut Windows'ta kesilip 'unexpected EOF' veriyor; kanca uzun_komut.py durduruyor, dosyayi Write ile yaz
kaynak: Kanallar/ortak_duzelt/heredoc_boy.py ciktisi 2026-11-18
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# bash-uzun-komut-8kb-1118

Olcum 11-18: tum Claude dokumlerinde 6951 heredoc'lu Bash komutu. Hata orani boya gore: 0-7 KB ~%0 (6809'da 1), 7-8 KB %31, 8-9 KB %90, 9 KB ustu %100. Sebep tirnak/heredoc degil, komut boyu (kucuk denemelerde tirnak, backtick, $(, EOF kelimesi hep gecti). Cozum araca gomuldu: ~/.claude/hooks/uzun_komut.py PreToolUse(Bash) 7500 bayt ustunu deny eder (113 hatanin 109'u, 6838 basaridan 16'si). Uzun betik/yama: Write ile dosyaya yaz, kisa komutla calistir. Olcum betigi Kanallar/ortak_duzelt/heredoc_boy.py.
