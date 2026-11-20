"""Private memory of Pocket over 60 sentences, per variant (argv[1]):
plain, gc (gc.collect after each), inference (state and generation in inference_mode)."""
import gc
import json
import re
import sys

import psutil
import torch
from pocket_tts import TTSModel

torch.set_num_threads(2)
P = psutil.Process()
mode = sys.argv[1]
m = json.load(open(r"C:\Users\meteh\testbench\outputs\PAR_1\_voice_output\voice_manifest.json", encoding="utf-8"))
sentences = [s for c in m["chunk_timeline"] for s in re.split(r"(?<=[.!?])\s+", c["text"]) if s][:60]
model = TTSModel.load_model(language="english")
ctx = torch.inference_mode() if mode == "inference" else torch.no_grad()
with ctx:
    voice = model.get_state_for_audio_prompt(m["reference_audio"])
start = P.memory_info().private / 2**20
for i, s in enumerate(sentences, 1):
    with ctx:
        model.generate_audio(voice, s)
    if mode == "gc":
        gc.collect()
    if i % 20 == 0:
        print(mode, i, "sentences: +%.0f MB" % (P.memory_info().private / 2**20 - start), flush=True)
