---
tur: ders
aciklama: For video dubbing translations (EN→TR), Claude in the main session translates; 3.8 Flash lost the 2026-11-03 comparison
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/dub-translator-claude.md
olusturma: 2026-11-03
guncel: 2026-11-03
yazan: auto-memory
onay: 
etiket: 
---
The user said that whichever of Claude or 3.8 Flash translates better becomes the standard translator. On 2026-11-03 the dub of video ciF-s9t63Qs (126 sentence lines, `testbench\dub_1101\v2`) was compared over the same 30 lines. Claude won:
- Flash left English words in the Turkish ("views", "faceless", "AI", "QA").
- Flash invented content: "Reddit" does not appear in the source.
- Flash mistranslated a word: facts → "gerçekler" instead of "kanıtlar".
- Flash went over the syllable budget on 2 of 30 lines; Claude on 0.

Flash 3.8-high also never finished all 126 lines: 9router timed out on large prompts after the 11-01 account bans (see [[antigravity-tos-ban]]).

**Why:** a dub needs exact meaning plus a length that fits each slot. Claude was better on both counts and costs no 9router quota.

**How to apply:** for dub/translation work, write the translation in the main session, sentence by sentence, at about 5 Turkish syllables per second of slot. Use `src/translate2.py` (9router) only as a fallback, with `CH=10` chunks.
