---
tur: ders
aciklama: Two agents installing/loading big TTS models at once froze the 16 GB PC (2026-10-31); run heavy model jobs one at a time
kaynak: auto-memory C--Users-meteh--gemini-scripts-documentary-materials/memory/no-parallel-model-loads.md
olusturma: 2026-10-31
guncel: 2026-10-31
yazan: auto-memory
onay: 
etiket: 
---
On 2026-10-31 two background agents (CosyVoice 2 + IndexTTS2) installed and loaded multi-GB models in parallel; the PC locked up and the session died. The user asked me to watch for this.

**Why:** 16 GB RAM, 4 GB VRAM — two model loads plus pip/uv builds exceed RAM.
**How to apply:** parallelize downloads/reading at most; any job that loads a model (TTS, VC, scoring) runs alone. Brief agents to check free RAM (<3 GB → stop) and to load the model once per process. Related: [[ses-zinciri]].
