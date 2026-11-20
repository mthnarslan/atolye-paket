---
tur: ders
aciklama: 11-19 alt ajan model ölçümü: 53 ajan, 46 sonnet / 5 opus / 2 fable / 0 haiku; Haiku hiç seçilmiyor çünkü varsayılan CLAUDE_CODE_SUBAGENT_MODEL=sonnet ve Agent çağrısında model yazılmıyor
kaynak: oturum 1b6742da 11-19
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: claude
onay: 
etiket: ortak
---
# alt-ajan-model-secimi-1119

Ölçüm (~/.claude/projects/*/*/subagents, 19 Kas): sonnet 46 ajan (cache okuma 204M, yeni girdi 12M, çıktı 2M), opus 5 (danışman), fable 2 (konsey), haiku 0. Sonnet işlerinin çoğu web araştırması/karşı-tez (doğru model); ~10'u Haiku'luk (yalnız okuma ≤40 satır cevap, deploy, hazır dedektör/turnuva koşturma, korpus toplama) ama token payı küçük (~%5-10). Asıl token yükü uzun araştırma ajanlarının 70-97 araç turunda biriken cache okuması. Önlem: oyun_plani.py istem notu 'modeli Agent çağrısında açık yaz: haiku = okuma/sayma/log/hazır komut/deploy' ve ajan:tip:model kaydı (state/oyun_log.jsonl). Ölçüm betiği: bu oturumun olc_model.py mantığı (subagents jsonl message.model + usage).
