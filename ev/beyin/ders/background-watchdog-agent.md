---
tur: ders
aciklama: During long production runs, start a background Sonnet watchdog subagent from the start that catches stalls/slowness and fixes them early
kaynak: auto-memory C--Users-meteh-Kanallar/memory/background-watchdog-agent.md
olusturma: 2026-11-06
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
At the start of any long multi-film production run, launch a background watchdog subagent (Sonnet) that tails the logs, checks RAM and hung LLM calls, and restarts only our own failed or stuck steps.

**Why:** the user said on 2026-11-06 that problems used to be solved late and time was wasted ("sorunları geç çözmeyelim").

**How to apply:** start the watchdog together with the queue, not after a problem shows up. Also try slow-path alternatives in parallel without being asked. See [[rearm-watchers]], [[fix-systemic-errors-proactively]].

Kullanici (6 Kas): film uretimi baslarken log/RAM/takilan LLM cagrisini izleyen ve sadece kendi surecimizi yeniden baslatan bir bekci alt ajan (Sonnet) bastan calissin; yavaslik gorunce alternatifleri paralel dene.
