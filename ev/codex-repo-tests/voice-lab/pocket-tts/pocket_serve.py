"""Kyutai Pocket TTS behind the same three endpoints as the Sopro service.

GET  /api/info        -> {"model": ..., "device": "cpu", "sample_rate": 24000}
POST /api/reference   raw float32 mono PCM (X-Sopro-Sample-Rate header) -> {"id": sha}
POST /api/synthesize  {"text", "reference", "seed", ...} -> raw float32 PCM at 24 kHz

sopro_voice_client talks to it unchanged when DOCUMENTARY_VOICE_ENGINE=pocket.
Pocket runs on the CPU (about 3x real time on one thread, measured
2026-10-27), so the voice no longer competes with picture scoring and NVENC
for the 4 GB card. One model serves one request at a time.
"""
import hashlib
import json
import os
import re
import socket
import tempfile
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import psutil
import soundfile as sf
import torch
import torchaudio
from pocket_tts import TTSModel

PORT = int(os.environ.get("POCKET_PORT", "7863"))
LANGUAGE = os.environ.get("POCKET_LANGUAGE", "english")
torch.set_num_threads(int(os.environ.get("POCKET_THREADS", "2")))
# Silence between the sentences of one chunk; chunks get 0.15 s from the client.
PAUSE = float(os.environ.get("POCKET_SENTENCE_PAUSE", "0.25"))



class Server(ThreadingHTTPServer):
    """Takes the port alone. Python's HTTPServer sets SO_REUSEADDR, which on
    Windows let four copies started at once by four films all listen on 7863
    (2026-10-27): 3 x 1.2 GB idle beside the one serving."""
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


# Bound before the model loads, so a second copy exits at once.
SERVER = Server(("127.0.0.1", PORT), BaseHTTPRequestHandler)
MODEL = TTSModel.load_model(language=LANGUAGE)
LOCK = threading.Lock()
VOICES = {}
# Uploaded references are kept on disk, so a restarted service still knows
# the id a film's voice step got before the restart.
REFS = Path(__file__).parent / "refs"
# Pocket's process grows ~1.2 GB per film voiced and keeps it (its KV caches
# are sized per sentence; measured 2.1 -> 3.3 -> 4.5 GB, 2026-10-27). Past
# this, an idle service exits and the next request starts a fresh one.
# Four films voiced back to back never left it idle and it reached 7.8 GB
# (free RAM 62 MB, CONC_1..4); so it restarts between two requests, and the
# client sends a request the restart cut off once more.
RECYCLE_MB = float(os.environ.get("POCKET_RECYCLE_MB", "3500"))
IDLE_SECONDS = float(os.environ.get("POCKET_IDLE_SECONDS", "1"))
# darbogaz_1107/G_ram: Pocket held 1.2-3.5 GB for as long as the run lived after the voice was
# done. The client (sopro_voice_client.ensure_sopro_running) starts it on demand and the references
# are on disk (REFS), so an idle service can simply exit. 0 turns this off.
IDLE_EXIT_SECONDS = float(os.environ.get("POCKET_IDLE_EXIT_SECONDS", "240"))
ACTIVITY = {"busy": 0, "last": time.time()}
INFO = {"model": "kyutai/pocket-tts:" + LANGUAGE, "mode": "per-sentence", "pause": PAUSE, "device": "cpu", "sample_rate": MODEL.sample_rate,
        "threads": torch.get_num_threads()}


def _voice(key):
    """The voice state of an uploaded reference, rebuilt from disk after a restart."""
    if key in VOICES:
        return VOICES[key]
    found = sorted(REFS.glob(key + "_*.f32")) if REFS.is_dir() else []
    if not found:
        return None
    rate = int(found[0].stem.rsplit("_", 1)[1])
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    try:
        sf.write(path, np.frombuffer(found[0].read_bytes(), dtype="<f4"), rate)
        with LOCK:
            VOICES[key] = MODEL.get_state_for_audio_prompt(path)
    finally:
        os.unlink(path)
    return VOICES[key]


def _exit_if_quiet():
    if ACTIVITY["busy"] == 0:
        print("recycling at %.0f MB" % (psutil.Process().memory_info().private / 2**20), flush=True)
        os._exit(0)


def _recycle():
    me = psutil.Process()
    while True:
        time.sleep(2)
        idle = time.time() - ACTIVITY["last"]
        if IDLE_EXIT_SECONDS > 0 and ACTIVITY["busy"] == 0 and idle > IDLE_EXIT_SECONDS:
            print("idle exit at %.0f MB after %.0f s idle" % (me.memory_info().private / 2**20, idle), flush=True)
            os._exit(0)
        if ACTIVITY["busy"] == 0 and idle > IDLE_SECONDS and me.memory_info().private / 2**20 > RECYCLE_MB:
            print("recycling at %.0f MB after %.0f s idle" % (me.memory_info().private / 2**20, idle), flush=True)
            os._exit(0)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, kind="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, data):
        self._send(code, json.dumps(data).encode("utf-8"))

    def do_GET(self):
        if self.path == "/api/info":
            return self._json(200, INFO)
        self._json(404, {"error": "not found"})

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        ACTIVITY["busy"] += 1
        try:
            return self._post(body)
        finally:
            ACTIVITY["busy"] -= 1
            ACTIVITY["last"] = time.time()
            # A film sends its sentences back to back, never leaving a quiet
            # moment; past the limit the service exits right after a reply
            # (already sent whole: the handler writes unbuffered).
            if ACTIVITY["busy"] == 0 and psutil.Process().memory_info().private / 2**20 > RECYCLE_MB:
                _exit_if_quiet()

    def _post(self, body):
        try:
            if self.path == "/api/reference":
                rate = int(self.headers.get("X-Sopro-Sample-Rate") or 24000)
                key = hashlib.sha256(body + str(rate).encode()).hexdigest()
                REFS.mkdir(exist_ok=True)
                saved = REFS / ("%s_%d.f32" % (key, rate))
                if not saved.is_file():
                    saved.write_bytes(body)
                _voice(key)
                return self._json(200, {"id": key})
            if self.path == "/api/synthesize":
                req = json.loads(body)
                voice = _voice(req["reference"])
                if voice is None:
                    return self._json(400, {"error": "unknown reference; upload it again"})
                # One sentence per call: given a whole chunk, Pocket repeated
                # or swapped words in 11 of 12 tries ("one to the left, one
                # to the left", "great white white"); sentence by sentence,
                # 0 of 12 (glitch_test.py, 2026-10-27).
                gap = np.zeros(int(PAUSE * MODEL.sample_rate), dtype=np.float32)
                parts = []
                with LOCK:
                    for sentence in re.split(r"(?<=[.!?])\s+", req["text"].strip()):
                        if not sentence:
                            continue
                        torch.manual_seed(int(req.get("seed", 42)))
                        parts += [MODEL.generate_audio(voice, sentence).numpy().reshape(-1), gap]
                audio = np.concatenate(parts[:-1])
                if MODEL.sample_rate != 24000:
                    audio = torchaudio.functional.resample(torch.from_numpy(audio), MODEL.sample_rate, 24000).numpy()
                return self._send(200, audio.astype("<f4").tobytes(), "application/octet-stream")
            self._json(404, {"error": "not found"})
        except Exception as exc:  # the client sees the reason instead of a dropped socket
            self._json(500, {"error": "%s: %s" % (type(exc).__name__, exc)})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print("pocket service on", PORT, INFO, flush=True)
    SERVER.RequestHandlerClass = Handler
    threading.Thread(target=_recycle, daemon=True).start()
    SERVER.serve_forever()
