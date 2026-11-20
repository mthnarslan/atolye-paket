"""Score Sopro's and Pocket TTS's PAR_1 chunks against the reference narrator.

Speaker similarity: cosine of SpeechBrain ECAPA embeddings (VoxCeleb), each
chunk against the reference recording. Accuracy: faster-whisper base.en
transcript against the chunk text (word error rate). Writes
compare/PAR_1/scores.json and prints the means.
"""
import json
import sys
import re
from pathlib import Path

import jiwer
import numpy as np
import soundfile as sf
import torch
import torchaudio
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import EncoderClassifier

OUT = Path(__file__).parent / "compare" / ("PAR_1" + (("_" + sys.argv[1]) if len(sys.argv) > 1 else ""))


def load16k(path):
    audio, sr = sf.read(str(path), dtype="float32", always_2d=True)
    wav = torch.from_numpy(audio.mean(axis=1))
    return torchaudio.functional.resample(wav, sr, 16000) if sr != 16000 else wav


def norm(text):
    return re.sub(r"[^a-z0-9' ]+", " ", text.lower()).split()


def main():
    timing = json.loads((OUT / "timing.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path(r"C:\Users\meteh\testbench\outputs\PAR_1\_voice_output\voice_manifest.json")
                          .read_text(encoding="utf-8"))
    enc = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb",
                                         savedir=str(Path(__file__).parent / "ecapa"))
    asr = WhisperModel("base.en", device="cpu", compute_type="int8")

    def emb(path):
        with torch.inference_mode():
            e = enc.encode_batch(load16k(path).unsqueeze(0)).reshape(-1)
        return e / e.norm()

    ref = emb(manifest["reference_audio"])
    rows = []
    for c in timing["chunks"]:
        row = {"id": c["id"]}
        for name, path in (("sopro", c["sopro"]), ("pocket", OUT / ("pocket_%02d.wav" % c["id"]))):
            row[name + "_sim"] = round(float(emb(path) @ ref), 3)
            said = " ".join(s.text for s in asr.transcribe(load16k(path).numpy(), language="en", beam_size=1)[0])
            row[name + "_wer"] = round(jiwer.wer(" ".join(norm(c["text"])), " ".join(norm(said)) or "x"), 3)
        rows.append(row)
        print(row, flush=True)
    summary = {k: round(float(np.mean([r[k] for r in rows])), 3)
               for k in ("sopro_sim", "pocket_sim", "sopro_wer", "pocket_wer")}
    summary["pocket_worst_wer"] = max(rows, key=lambda r: r["pocket_wer"])
    summary["sopro_worst_wer"] = max(rows, key=lambda r: r["sopro_wer"])
    (OUT / "scores.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1), encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
