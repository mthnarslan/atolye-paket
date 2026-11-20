---
tur: ders
aciklama: Prod Chatterbox venv (voiceclone_1031/engines/chatterbox/.venv, Jeff :7864) 11-17'de silinmis bulundu; yeniden kurulum tarifi
kaynak: wa1117 ornek
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: ortak
---
# chatterbox-venv-silinmis-1117

11-17: .venv yoktu (sebep bilinmiyor; Jeff sesi :7864 de bunu kullanir). Yeniden kurulum ~35 dk (torch 2.5 GB): py -3.12 -m venv; torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124; chatterbox-tts==0.1.7 soundfile. Kontrol: import torch,chatterbox -> OK 2.6.0+cu124 True. pip -q ile log 15 dk sessiz kalir, bekci TAKILDI der: -q kullanma ya da pid ile bekle. Global python chatterbox import'u huggingface_hub ResolvedRevision hatasi verir, kullanma. Tarif: hf/wa1117/ornek/kur_cb.sh
