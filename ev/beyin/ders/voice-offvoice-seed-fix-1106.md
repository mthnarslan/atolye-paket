---
tur: ders
aciklama: Ses denetimi reference_voice_match FAIL (kind=voice): otomatik tamir sadece text sorunlarini onarir; testbench\speed_1106\voicefix.py ayni metin + yeni seed ile o parcayi yeniden urettirir
kaynak: EP02 fullrun 1106b
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: claude
onay: 
etiket: 
---
# voice-offvoice-seed-fix-1106

Belirti: Pocket+Jeff ref, EP02 1106: 'Spotters had seen it!' (296 sn) ve 'Trees with trunks...' (323 sn) ince/kadinsi sese kaydi, stage 1 FAIL criteria reference_voice_match. documentary_voice_repair.repair_targets yalniz kind=text ve voice_match PASS iken calisir, yani ses kaymasi icin repair_rounds=0. Cozum (.gemini'ye dokunmadan): voice_repair_state.json overrides {chunk_id: {text: ayni, seed: +53}} (run_step1 validated_overrides ile okur), master_voiceover.wav + voice_audit.json'u kenara al, stage 1'i yeniden kos: sadece o parcalar uretilir, digerleri chunk onbellekten. Arac: python C:\Users\meteh\testbench\speed_1106\voicefix.py <CodexOutputs film> --apply. Kalici duzeltme onerisi: repair_targets'a kind=voice icin seed degistirme (kullanici izniyle .gemini).
