---
tur: ders
aciklama: User wants an Opus 5.5 medium main session and cheaper subagents (Sonnet by default, Haiku for trivial sweeps) to save usage limits
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/commander-subagent-models.md
olusturma: 2026-10-30
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
On 2026-10-29 the user asked for this split: the main session stays on Opus 5.5 at medium effort, and high effort is not needed. Subagents should run on cheaper models.

This is configured in `~/.claude/settings.json`: `env.CLAUDE_CODE_SUBAGENT_MODEL = "sonnet"` (the FORCE variable is deliberately not set), `enableArtifact: false` and `showClearContextOnPlanAccept: true`.

**Why:** usage limits are the user's main worry as conversations grow and they run 3–4 sessions in parallel. /doctor found that long sessions (8 h+) are the main cost and that general-purpose subagents made up 26% of usage.

**How to apply:**
- Delegate searches, reads and test runs to subagents and let them default to Sonnet. Pass `model: "haiku"` for trivial file sweeps. Pass `model: "opus"` only for hard diagnosis or design review.
- Suggest a fresh session when the topic changes.
- Tool-output compression is not wanted for pipeline debugging; see [[token-saver-tools]].

**Workflow caveat (2026-10-30):** the `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` env also applies to Workflow `agent()` calls that omit `model`. The "Opus max" architecture workflow wf_273ca692 actually ran every agent on Sonnet 5.5; only the effort setting took effect. When the user asks for Opus inside a workflow, set `model: 'opus'` on those `agent()` calls.

**Ana model:** ana oturum Opus medium kalir; kullanici (2026-10-30) Sonnet'e gecmeyecegini soyledi, token tasarrufu olarak onerme (tasarruf: daha az ana oturum cagrisi, supervisor/ajan olayinda uyanma, Sonnet alt ajan).
