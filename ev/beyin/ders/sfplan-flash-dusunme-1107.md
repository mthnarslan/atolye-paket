---
tur: ders
aciklama: sf plan yavasligi = Flash-low gizli dusunme (12-24k token, 154-210 sn/parca); reasoning_effort=minimal ile 5-12 sn, EP03 1118->85 sn
kaynak: testbench/darbogaz_1107/P_sfplan/RESULT.md
olusturma: 2026-11-07
guncel: 2026-11-07
yazan: claude
onay: 
etiket: 
---
# sfplan-flash-dusunme-1107

Kok: istem boyutu degil, Flash'in gorunmeyen dusunme gecisi; 75 sn zaman asimi hic yetmiyordu (35 check timed out). Cozum sf.py: minimal reasoning + lint + tek onarim turu, sert hatada eski yola dus; klip kontrolu 4'lu toplu; jparse; parca onbellegi. Kalite: sahne sayisi %7 icinde, klip kararlari 70/78 ayni, hic kotu<->temiz donusu yok. Kapatma SF_PLAN_FAST=0. Ayni ders diger Flash-low cagrilarina da uygulanabilir (ilk bakilacak yer: dusunme tokeni).
