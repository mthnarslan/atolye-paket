"""Voice PAR_1's 31 Sopro chunks again with Pocket TTS on the CPU, same reference.

Writes compare/PAR_1/pocket_NN.wav, a joined pocket_full.wav and timing.json
(load, voice-prompt and per-chunk synthesis seconds, real-time factor).
Usage: .venv\\Scripts\\python compare_par1.py [language]
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from pocket_tts import TTSModel

MANIFEST = Path(r"C:\Users\meteh\testbench\outputs\PAR_1\_voice_output\voice_manifest.json")
OUT = Path(__file__).parent / "compare" / ("PAR_1" + (("_" + sys.argv[1]) if len(sys.argv) > 1 else ""))


def main():
    language = sys.argv[1] if len(sys.argv) > 1 else None
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    chunks = manifest["chunk_timeline"]
    OUT.mkdir(parents=True, exist_ok=True)
    t = time.time()
    model = TTSModel.load_model(language=language) if language else TTSModel.load_model()
    load_s = time.time() - t
    t = time.time()
    voice = model.get_state_for_audio_prompt(manifest["reference_audio"])
    prompt_s = time.time() - t
    rows, parts = [], []
    for c in chunks:
        t = time.time()
        audio = model.generate_audio(voice, c["text"]).numpy().reshape(-1)
        secs = time.time() - t
        path = OUT / ("pocket_%02d.wav" % c["id"])
        sf.write(path, audio, model.sample_rate)
        parts += [audio, np.zeros(int(0.25 * model.sample_rate), dtype=audio.dtype)]
        rows.append({"id": c["id"], "text": c["text"], "seconds": round(secs, 2),
                     "audio_seconds": round(len(audio) / model.sample_rate, 2), "sopro": c["path"]})
        print(c["id"], rows[-1]["seconds"], rows[-1]["audio_seconds"], flush=True)
    sf.write(OUT / "pocket_full.wav", np.concatenate(parts), model.sample_rate)
    synth = sum(r["seconds"] for r in rows)
    audio_total = sum(r["audio_seconds"] for r in rows)
    report = {"language": language or "default", "threads": torch.get_num_threads(), "load_seconds": round(load_s, 1),
              "prompt_seconds": round(prompt_s, 1), "synthesis_seconds": round(synth, 1),
              "audio_seconds": round(audio_total, 1), "realtime_factor": round(audio_total / synth, 2),
              "sopro_synthesis_seconds": manifest["synthesis_time_sec"],
              "sopro_audio_seconds": manifest["raw_duration_sec"], "chunks": rows}
    (OUT / "timing.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "chunks"}), flush=True)


if __name__ == "__main__":
    main()
