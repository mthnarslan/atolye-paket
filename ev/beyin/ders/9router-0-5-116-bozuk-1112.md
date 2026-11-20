---
tur: ders
aciklama: 9router 0.5.116 Node 22.19+ ister (undici 8); VDS'te Node 20 ile 500 'reading bind'. Cozum: /opt/node22 + pm2 interpreter; 11-12 prod 0.5.116 Node 22.23.5 ile calisiyor
kaynak: oturum 2026-11-12; oturum 2026-11-12
olusturma: 2026-11-12
guncel: 2026-11-12
yazan: claude
onay: 
etiket: 
---
# 9router-0-5-116-bozuk-1112

11-12: servis global degil /opt/9router/node_modules/9router'dan calisir (pm2), bu yuzden 'npm i -g' etkisizdir; guncelleme 'cd /opt/9router && npm i 9router@<surum>' + pm2 restart. 0.5.116 acildi ama istekler 500. Geri donus: npm i 9router@0.5.112 (postinstall fix-sqljs.sh), ~3 dk kesinti. Yedekler /root/data.sqlite.bak-1112-preupdate, package.json.bak-1112. Global kurulum 0.5.116 kaldi (kullanilmiyor). Yeni surumu denemeden once node surumu/yayin notuna bak, parti yokken dene. Ayrica /root/scan_all_quotas.py kota yuzdesini yanlis okur (hep %100); gercek kota panelde: 11-12 ejderha582 %1, metehankahraman099 %1, hamidnezamzade66 %81, metehankahraman077 %89 haftalik.

## 2026-11-12 (claude)

Sebep: 0.5.116 app/node_modules'a undici 8.12.3 getiriyor (engines node>=22.19.0); sistem Node 20.20.2 -> her istekte TypeError reading 'bind'. Cozum 11-12: resmi node-v22.23.5 tarball (sha256 dogrulandi) /opt/node22'ye; ecosystem.config.cjs'e interpreter: /opt/node22/bin/node (yedek ecosystem.config.cjs.bak-claude-20261112); PATH=/opt/node22/bin ile 'npm i 9router@0.5.116' + 'npm rebuild better-sqlite3' (native modul Node 22 ABI); pm2 delete + start ecosystem + save. Test: ayri klasor /opt/9r-test, port 20199, veri kopyasi; flash-low/high 200. Sistem node'u 20 kaldi. Dikkat: servis /opt/9router/node_modules/9router'dan calisir, 'npm i -g' etkisiz. Gelecek guncelleme: PATH=/opt/node22/bin ile cd /opt/9router && npm i 9router@X && npm rebuild better-sqlite3 && pm2 restart 9router. Geri donus yedekleri /root/data.sqlite.bak-1112-node22, package*.bak-1112b. Uzak komutta 'pkill -f <yol>' ssh kabugunu da oldurur (komut satiri ayni yolu icerir).
