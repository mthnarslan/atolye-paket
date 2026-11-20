---
tur: ders
aciklama: "Thumbnails: user likes BOTH v7 (rival-pattern / real-frame) and v8 (captcha oddness) styles; keep 3 perspectives per video, never collapse to one flow"
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/cover-perspectives.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: auto-memory
onay: 
etiket: 
---
User (2026-11-19) liked both the v7 covers (built from hit rivals' pattern, some from our real frames) and the v8 covers (captcha-oddness idea, mixed sources: AI / real frame / Commons / graphic). They know the two differ and see that difference as good. Keep per video: Yayındaki + v7 + v8 (3 perspectives). Criticism: covers that all come from one "flat flow" look alike.

**Why:** objective measures (ayrışma, clutter, OCR legibility, saliency) failed to predict hits among 144 rivals; taste signal comes from the user's own likes on the site (/api/begen, D1 key `kapak:begen`).

**How to apply:** new cover rounds produce several distinct approaches per video, not one template; read the user's likes (`npx wrangler d1 execute ortak-atolye --remote --command "SELECT v FROM kv WHERE k='kapak:begen'"`) to learn what they like before the next round. Related: [[value-over-variety]], [[ortak-atolye-site]].
