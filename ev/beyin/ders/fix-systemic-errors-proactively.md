---
tur: ders
aciklama: When a background job hits a systemic error (e.g. 9router 503), find and fix it immediately — never wait for the user to notice
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/fix-systemic-errors-proactively.md
olusturma: 2026-11-01
guncel: 2026-11-01
yazan: auto-memory
onay: 
etiket: 
---
If any running job shows a systemic error (same error repeating, API 503/403, downloads failing), go find the root cause and keep working until the system is healthy again — without waiting for the user to ask.

**Why:** 2026-11-01 9router returned 503 for 20+ min (upstream 403 on flash-medium/high) while I waited for task notifications; the user discovered it by asking "video nerde" and was angry the deliverable kept slipping.

**How to apply:** Long background jobs must surface failures to me — check error counts when a job is launched and at each wake; a background job that silently retries errors is not "running fine". Related: [[rearm-watchers]], [[gpt-replacement-model]].
