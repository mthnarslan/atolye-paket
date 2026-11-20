---
tur: ders
aciklama: bekci.py -- bash -c WSL'e gider; Git Bash'ten 'cmd /c' de bozulur (/c -> C:/ dönüşümü): npx.cmd / python / curl.exe doğrudan ver
kaynak: hf/isaac2; hf/isaac2
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: ortak,bekci
---
# bekci-bash-c-wsl-1113

13 Kas: bekci.py içinden 'bash -c' çağrısı System32 bash.exe (WSL) açtı, yollar bulunamadı. Çözüm: bekci'ye doğrudan exe ver (python ..., cmd /c npx ..., curl.exe), ya da Git Bash'in tam yolunu kullan.

## 2026-11-13 (claude)

13 Kas: (1) bekci.py içinden 'bash -c' System32 bash.exe (WSL) açtı. (2) Git Bash'ten 'bekci.py -- cmd /c npx ...' verince MSYS '/c'yi 'C:/' yaptı, cmd etkileşimli açılıp çıktı (iş hiç koşmadı, çıkış 0!). Çözüm: exe'yi doğrudan ver: npx.cmd, python, curl.exe; gerekirse 'cmd //c'.

**16 Kas – koda gömüldü:** 14–16 Kas arası ders yazılıyken 2 oturum 5 kez yine `bekci.py -- bash -c` çağırdı. Artık `bekci.py` Windowsta