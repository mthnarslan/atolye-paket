---
tur: ders
aciklama: OmniVoice dublaj hizi: isinmis modelde batch kazanc vermiyor; num_step 16->12 %20 hizli, kalite ayni
kaynak: testbench/dub_hiz_1113/out/*_bc.json, kanit/*_gen.txt
olusturma: 2026-11-13
guncel: 2026-11-13
yazan: claude
onay: 
etiket: 
---
# dub-hiz-adim-1113

testbench/dub_hiz_1113, 32 cumle x 3 tekrar. s/cumle (r1 soguk haric isinmis): A(16 adim, tekli) 1,65; B4 1,77; B8 1,74; N12(12 adim) 1,32; N10 1,15. Whisper bc: A 0/96 kotu, N12 1/96 (P(tr) 0,79 sinirda), N10 3/96. r1'deki A 6,71 sn model isinma/derleme etkisiydi, batch kazanci sanilmasin. Uygulandi: dub_1112/v2/gen.py num_step=DUB_STEPS (varsayilan 12).
