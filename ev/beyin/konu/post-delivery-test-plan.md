---
tur: konu
aciklama: Teslim sonrasi test plani sonuclari: ses referansa uymali (benzerlik+ASR+kulak), Pocket SO_REUSEADDR/3.5 GB, NVENC 4 slot, 4 film paralel sonucu
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/post-delivery-test-plan.md
olusturma: 2026-10-28
guncel: 2026-11-08
yazan: auto-memory
onay: 
etiket: 
---
Kullanici (2026-10-26) plani: 9 ZIP teslimi sonrasi (1) calisan sistemi yedekle, (2) ayri temiz kopyada (testbench `C:\Users\meteh\testbench`, kopru :8199) ucdan uca test, (3) acik basari hedefleri koy, sonra daha iyi sisteme gec. **Yapildi (2026-10-27):** 9 ZIP teslim edildi, yedek `C:\Users\meteh\Backups\2026-10-27_pre_speedup`, testbench kuruldu, Pocket TTS prod'a girdi.

**Kalan kurallar:**
- **Ses kullanicinin tek korkusu:** TTS degisikligi referans anlaticiyla ayni kaliteyi korumali; sec: konusmaci benzerligi (ECAPA) + ASR dogrulugu + kulak ornekleri (Pocket benzerlikte 0,751 vs Sopro 0,838 cikti ama kullanici kulakla onayladi). Ses GPU'da hiz darbogazi degil, sorun guvenilirlikti.
- **Pocket (:7863):** 4 kopya ayni porta baglanmisti (SO_REUSEADDR) -> exclusive bind; ~12 MB/cumle buyur, 3.5 GB asinca yanit sonrasi cikar, istemci bir kez yeniden dener; cumle bazli sentez (butun chunk kelime tekrari yapti).
- **BBC kesimleri** 24 NVENC ffmpeg yaratip RAM'i bitirdi -> 4 global slot; kesik npz kutuphaneyi bozdu -> atomik yazim + kenara alma.
- **4 film paralel (conc4b):** hepsi 76 dk'da bitti, ses fazinda min bos RAM 2,8 GB (eskiden 62 MB); ses 5,5 dk'da hazir; uctan uca 151 shot/sa vs 85 (eski seri-ses akisi ~90-108 dk).
- ZERO PULSE G-Labs: ~1400 varlik/gece sonrasi "Max Retries"; 10 paralelde UNUSUAL_ACTIVITY -> 3 isle devam.
Ilgili: [[youtube-gate]], [[ses-zinciri]].

## 2026-11-08 (auto-memory guncellemesi: C--Users-meteh--gemini-scripts-documentary-materials)

User (2026-10-26): once every ZIP is delivered, (1) back up the working system untouched, (2) run serious end-to-end tests in a separate clean copy, (3) set explicit success targets and test every stage continuously until they are met, only then switch to better systems (40 films/day goal, Argon plan in docs/ARGON_ANALIZ_2026-10-26.md). Voice is the user's one fear: any TTS change must keep the same quality and match the reference narrator voice (measure speaker similarity + ASR accuracy + listening samples against Sopro before switching). Other stages the user leaves to me.

Done 2026-10-27: all 9 ZIPs delivered; backup at C:\Users\meteh\Backups\2026-10-27_pre_speedup; test bench C:\Users\meteh\testbench (bridge port 8199, CODEX_OUTPUT_ROOT/DOCUMENTARY_DELIVERY_ROOT env, bench_run.py, 3-min TEST_A films). Measured: baseline stage 3 46.6 s/accepted shot, speed7 candidate 32.2 s (-31%), film 38 -> 23 min; candidate merged to production main (9b98fb2). Top-3 single-Flash pick (branch top3 in testbench clone, cdf66a5) cut renders/LLM calls but not total time and left 1 shot unresolved - parked.

Still pending decisions: Pocket TTS (HF gated terms the user must accept), the 40/day architecture session card, BBC library float16 memmap (catalog rebuild), the unmerged 7-speed-fix branch (worktree-agent-a130fc8ba44bd86c1 + c93ca83 non-BBC-from-start). Source-credit lists (scratchpad credits.py) parked at the user's request.

2026-10-27 Pocket TTS test (venv voice-lab/pocket-tts/.venv, HF account Derebey has kyutai/pocket-tts access): PAR_1 31 chunks, ECAPA similarity to reference Sopro 0.838 vs Pocket 0.751 (english_2026-10 0.748, 24l 0.761), WER Sopro 4.1% vs Pocket 3.2%; Pocket 2.9x realtime on 1 CPU thread, Sopro 9x on GPU (17.5 s for 158 s). Pocket fails the similarity bar; listening samples in voice-lab/pocket-tts/compare/DINLE. Voice is not a speed bottleneck on GPU; its problem was reliability.
CPU run2 (par4_run2, 174.2 shots/h, free RAM min 2371 MB, 0 libx264): bridge python ~12% of machine, short-lived processes (ffmpeg/ffprobe) ~51%, other apps ~22%. SSL per-request reload was ~20% of bridge samples (fixed c3d3c53). Production main now c3d3c53 incl. nvencwait 25aae37.

2026-10-27 Pocket TTS in production: user approved the voice by ear. scripts 7b8d7bb (DOCUMENTARY_VOICE_ENGINE=pocket set with setx; service voice-lab/pocket-tts/pocket_serve.py port 7863, Start-Pocket.ps1, per-sentence synthesis because whole chunks repeated words 11/12). Bridge no longer stops Pocket after a film; batch_films skips voice.lock for pocket. Concurrent test conc4 (all 4 films start stage 1-4 at once): all voices done in 5.5 min first try, 3 films delivered in 53-55 min wall vs ~90-108 min old serial-voice flow; end-to-end 151 accepted shots/h vs 85. CONC_1 (shark topic) failed on 1 unresolved shot after 61 min (footage scarcity tail). Free RAM min 456 MB. Defender exclusions added by user; other-apps CPU 22% -> 12%.

2026-10-27 evening RAM work: 4 Pocket copies bound one port (SO_REUSEADDR) -> exclusive bind; Pocket grows ~12 MB/sentence -> exits right after a reply past 3.5 GB, refs kept on disk, client retries once (scripts a917772). Bridge reloads modules under a lock (8c4ce53). BBC library: truncated npz broke library for every film since 04:11 -> atomic write + set-aside (93375ef); BBC cuts fanned out 24 NVENC ffmpegs (12.8 GB, free RAM 2 MB) -> 4 global slots (62b92a2, not yet measured). conc4b: all 4 films done in 76 min, 171 shots, voice-phase min free RAM 2.8 GB (was 62 MB). ZERO PULSE (OneDrive\Desktop\Yeni klasör) tts_sopro.py pinned to Sopro because of the user-wide pocket env; report SISTEM_RAPORU_2026-10-27.md there.

2026-10-27/28 SkullStudio (C:\Users\meteh\SkullStudio, git): ZERO PULSE episodes from material folders (new_episode.py -> run_episode.py / batch.py). EP02-EP09 delivered overnight (out/final.mp4). Lessons fixed in code: caption-first panels drawn as headline; caption text under kind key; cutaway hold to next panel; Omni Flash 2x2 grid clips (gridcheck.py); Flash error bodies in cutaway codegen; build8 RAM (NPARTS 6, x264 -threads 4); words_ts on GPU; blankcheck.py for white frames. G-Labs limits: ~1400 assets/night then "Max Retries Exceeded", and Google "PUBLIC_ERROR_UNUSUAL_ACTIVITY_TOO_MUCH_TRAFFIC" at 10 parallel jobs -> gen2 stops after 12 failures in a row; resume at 3 jobs (episodes/resume_slow.sh).
