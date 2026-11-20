"""Does sentence-by-sentence synthesis stop Pocket's repeated words?

The two chunks the voice audit failed on POCKET_1, each voiced with 6 seeds
as a whole chunk and split into sentences; faster-whisper checks the words.
"""
import re
import sys

import jiwer
import numpy as np
import torch
import torchaudio
from faster_whisper import WhisperModel
from pocket_tts import TTSModel

REF = r"C:\Users\meteh\testbench\films\POCKET_1\TOPIC_03_ORCA_SHARK_FIRST_30_SECONDS.wav"
TEXTS = [
    "At about the same time, two male killer whales started showing up along that coast. Their dorsal fins are bent over, one to the left, one to the right.",
    "Let's go through what the evidence actually shows. To understand why this was such a shock, you need to understand how dominant the great white was here.",
]


def norm(t):
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", t.lower()).split())


def main():
    model = TTSModel.load_model(language=sys.argv[1] if len(sys.argv) > 1 else "english")
    voice = model.get_state_for_audio_prompt(REF)
    asr = WhisperModel("base.en", device="cpu", compute_type="int8")
    for mode in ("chunk", "sentences"):
        bad = 0
        for text in TEXTS:
            parts = [text] if mode == "chunk" else re.split(r"(?<=[.!?])\s+", text)
            for seed in range(6):
                audio = []
                for part in parts:
                    torch.manual_seed(seed)
                    audio.append(model.generate_audio(voice, part).numpy().reshape(-1))
                    audio.append(np.zeros(int(0.15 * model.sample_rate), dtype=np.float32))
                wav = torchaudio.functional.resample(torch.from_numpy(np.concatenate(audio)), model.sample_rate, 16000).numpy()
                said = " ".join(s.text for s in asr.transcribe(wav, language="en", beam_size=5)[0])
                wer = jiwer.wer(norm(text), norm(said))
                bad += wer > 0.05
                if wer > 0.05:
                    print(mode, seed, round(wer, 3), "|", said.strip(), flush=True)
        print("MODE", mode, "bad", bad, "of", 6 * len(TEXTS), flush=True)


if __name__ == "__main__":
    main()
