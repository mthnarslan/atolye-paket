---
tur: ders
aciklama: YouTube kaynaklı mp4'ü -c copy ile HLS'e bölünce bazı videolarda (2/10) segmentlerde PPS eksik; NVENC ile yeniden kodla
kaynak: testbench/dub10_1114
olusturma: 2026-11-14
guncel: 2026-11-14
yazan: claude
onay: 
etiket: 
---
# hls-copy-pps-1114

dub10_1114: v07/v08 out.mp4 -c copy -f hls -> s050.ts 'non-existing PPS 0 referenced' (seek'te bozuk görüntü). dump_extra bsf hata veriyor. Çözüm: h264_nvenc -preset p4 -cq 23 -force_key_frames expr:gte(t,n_forced*6). Kontrol: ffmpeg -v error -i sXXX.ts -f null - | grep -c PPS, her dub için 3 segment. Ayrıca dub hattı ölçümü: 10 video/146 dk ses -> ASR large-v3 ~35 dk, stage2 (OmniVoice 12 adım+bc2+demucs+mix) ~2 sa (12:48-14:44), 4 Sonnet çeviri ajanı ASR ile paralel.
