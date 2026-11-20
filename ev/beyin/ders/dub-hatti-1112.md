---
tur: ders
aciklama: Dublaj hatti testbench/dub_1112'de yeniden kuruldu: refC sesi ~8,5 hece/sn konusur, tum videoya tek tempo (0,9-0,97) ile oturtulur; site Dublajlar sekmesi /v/dublaj.json
kaynak: oturum 2026-11-12, testbench/dub_1112
olusturma: 2026-11-12
guncel: 2026-11-12
yazan: claude
onay: 
etiket: 
---
# dub-hatti-1112

11-10 disk temizliginde dub_1107/dub_1101 silindi; betikler oturum kaydindan testbench/dub_1112/src'ye geri kuruldu (dl.py yt_gate ile indirir, asr_words large-v3 int8_float16, isl_words, build_segs PRON, omni_multi language='tr', mix.py DUB_TEMPO, backcheck). Ses: testbench/asker_tr_1111/ref/refC.wav+txt (Turkce yayinci). Bu ses 6 degil ~8,5 hece/sn konusur: 6 hece/sn hedefli ceviri adalari %20-25 erken bitirir. Cozum satir bazli hiz degil, tum videoya tek atempo: yavas konusmaci 0,90-0,93, hizli konusmaci 0,97 (0,9'da 4 sn gecikme birikti). Ceviriyi 7-7,5 hece/sn hedefle yaz, kisaltma. Tuzaklar: bekci '-- bash x.sh' WSL bash'i bulur, Git Bash tam yolu ver; GPU baska isle doluyken float16 ASR 11 dk ciktisiz kaldi, int8_float16 2x gercek zaman; large-v3-turbo onbellekten silinmis. Geri dinleme 181 adada 1 gercek hata buldu (degil yutulmus). Site: ortak-site tools/yeni_ana.tpl.html Dublajlar sekmesi, liste public/v/dublaj.json, video HLS public/v/dub-<ad>/.
