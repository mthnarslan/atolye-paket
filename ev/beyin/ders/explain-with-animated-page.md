---
tur: ders
aciklama: User prefers proposals/analyses explained as an animated local web page instead of long chat text
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/explain-with-animated-page.md
olusturma: 2026-10-29
guncel: 2026-10-29
yazan: auto-memory
onay: 
etiket: 
---
When explaining ideas, findings or proposals (video studies, system changes), build a local HTML page with step-by-step animations and examples (▶ Oynat per section, "Bugün / Kurulursa" boxes) instead of long text. Keep the chat reply short and point to the page.

**Why:** 2026-10-29 the user said long texts are hard to follow; watching an animation of "what we use for what" makes the ideas concrete for them.

**How to apply:** pages go under `C:\Users\meteh\.gemini\yt_study\site\` (first: `index.html`, GitHub Trending #56). Serve with `python -m http.server 8433 --bind 127.0.0.1` from that folder (file:// in the browser pane is a static snapshot, JS doesn't run). The pane may block requestAnimationFrame, so animate with setTimeout. Label illustrative data as "örnek"; never invent facts. Related: [[yt-study-flow]].
