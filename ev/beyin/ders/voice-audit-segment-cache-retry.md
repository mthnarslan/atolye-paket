---
tur: ders
aciklama: Ses denetimi: geçen segmentler voice_gemini_cache'te saklanıyor, 5xx/timeout'ta 4 deneme+geri çekilme; drive transport-only hatada exit 13 ile kendisi yeniden kuyruğa alıyor
kaynak: EP02-EP05 partisi
olusturma: 2026-11-05
guncel: 2026-11-05
yazan: claude
onay: 
etiket: 
---
# voice-audit-segment-cache-retry

Önce: segment başına 1 deneme + 1 anlık diğer hat, backoff yok; 503 → PASS_DEGRADED/UNVERIFIED, drive exit 1, elle restart (EP02 6 kez). Yama (5 Kas, testbench/voice_audit_resilience_1105): sadece iki kriter de PASS olan segment önbelleğe; eşik/istem değişmedi. Test stub'ı calls[-1] ile segment okuyordu, threadler yarıştı → sahte FAIL; payload'dan indeks oku.
