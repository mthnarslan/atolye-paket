---
tur: ders
aciklama: VDS'e is tasima: Tailscale ~0,5-0,6 MB/s (relay, 119 ms); sadece ses ASR'si (base.en int8, 4x hizli, opus 24k yukleme) degerli; ffmpeg probe ve SigLIP tasinmaz
kaynak: testbench/vds_offload_1105
olusturma: 2026-11-05
guncel: 2026-11-05
yazan: claude
onay: 
etiket: 
---
# vds-offload-pilot-1105

120 sn dilim: yerel CPU 47 sn, VDS 12-14 sn, ~400 MB. Kelime uyumu %96,7 (CPU/GPU gurultusu). Probe: yukleme 25 sn vs yerel 1,6 sn -> tasima. SigLIP2 VDS'te 3,2 GB RSS (9router riski), torch 2.15 oneDNN divide error, mkldnn kapali 0,42 sn/kare -> tasima. Entegrasyon onerisi: documentary_voice_audit.py run_audit oncesi remote_asr + yerel geri donus. /opt/offload kurulu. Darbogaz ag; Tailscale direct baglanti kurulursa yeniden degerlendir.
