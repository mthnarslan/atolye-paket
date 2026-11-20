---
tur: ders
aciklama: Footage with a "license this footage" overlay must not be used; reviewer-passed license text is rejected by runner._deliverable_review (22084c7); crop/replace rule for delivered shots
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/no-license-watermark-clips.md
olusturma: 2026-11-01
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Never take clips whose picture carries a stock-footage sales overlay that says the video must be licensed: "Visit StormChasingVideo.com To License", "SCV", "Licensing: …", "To license this clip …", or a URL plus "license". The user flagged such a shot (07_00m25s_VIDEO, a storm film) on 2026-11-01.

**Why:** that footage is explicitly sold, so using it without a license is a rights problem the user does not want. Ordinary channel logos, news bugs and LIVE tags are still fine.

**How to apply:** implemented in prod d6a8a5c (2026-11-01). `io.LICENSE_OVERLAY_RULE` is added to the scan, frame-check, pick and review prompts. `sources.LICENSE_SELLERS` drops seller channels and titles at search time. The review's licence filter keeps "overlay" defects. If such a clip still slips through, extend the `LICENSE_SELLERS` regex or tighten the rule text there. Do not reintroduce "all watermarks fine" wording without this exception.

**Hakem lisans notunu gecirdi (5 Kas):** hakem 'NOT FOR BROADCAST', Alamy, Getty gibi yaziyi improvement_notes'a yazip blocking_defects bos birakarak PASS verdi; EP04/EP05'te 5 cekim boyle teslime girdi. Cozum prod 22084c7: `runner._deliverable_review`, not metninde lisans izi (not for (re)broadcast/resale, alamy/getty/dreamstime/shutterstock, seller watermark regex'i) gorunce teslim etmez; kimlik degismez, yeniden kullanimda da reddeder; temiz cekimlerde 0 yanlis pozitif. Teslimden sonra kontrol: shots/*/result.json review.data'da bu regex.
**Teslim edilmis cekimi kirparken:** result.json sha256 + source_start/end guncelle; kenar seridindeki yazi -> kirp, ortadaki yari saydam -> degistir. Ayni kayit iki kesimde >=30 sn ayri olmali (render_materials kapisi).
