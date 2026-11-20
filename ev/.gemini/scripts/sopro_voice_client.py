import urllib.error
import urllib.request
import json
import time
import subprocess
from pathlib import Path
import soundfile as sf
import numpy as np

import os

# DOCUMENTARY_VOICE_ENGINE=pocket points this client at the Kyutai Pocket TTS
# service (voice-lab/pocket-tts/pocket_serve.py, CPU), which speaks the same
# three endpoints; Sopro (GPU) stays the default.
ENGINE = os.environ.get("DOCUMENTARY_VOICE_ENGINE", "sopro").strip().lower()
_PORTS = {"pocket": 7863, "chatterbox": 7864}  # chatterbox: voice-lab/chatterbox/chatterbox_serve.py (Chatterbox Turbo, GPU)
_STARTS = {"pocket": "Start-Pocket.ps1", "chatterbox": "Start-Chatterbox.ps1"}
SOPRO_URL = "http://127.0.0.1:%d" % _PORTS.get(ENGINE, 7862)
START_SCRIPT = Path(r"C:\Users\meteh\codex-repo-tests\voice-lab") / _STARTS.get(ENGINE, "Start-Sopro.ps1")

def service_info():
    with urllib.request.urlopen(f"{SOPRO_URL}/api/info", timeout=5) as response:
        return json.loads(response.read())

def ensure_sopro_running():
    """Verify Sopro service is listening on port 7862, launch if needed."""
    try:
        req = urllib.request.Request(f"{SOPRO_URL}/api/info")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass

    # Launch via Start-Sopro.ps1
    print("[SOPRO] Sopro servisi ayakta degil, baslatiliyor...")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(START_SCRIPT)], check=True)
    
    # Wait for ready
    # A cold start loads the model onto the GPU and took over 90 s once the
    # service is stopped after each film's voice (stop_sopro).
    # Under four films' load the GPU it shares with SigLIP and NVENC made
    # the cold start pass 300 s (TOPIC_6, 2026-10-26).
    deadline = time.time() + 900
    relaunch = time.time() + 60
    while time.time() < deadline:
        # The start script skips a port still held by a service that is
        # exiting (a Pocket restart); try it again once that one is gone.
        if time.time() > relaunch:
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(START_SCRIPT)])
            relaunch = time.time() + 60
        try:
            req = urllib.request.Request(f"{SOPRO_URL}/api/info")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print("[SOPRO] Servis basariyla baglandi!")
                    return True
        except Exception:
            time.sleep(1)
            
    raise RuntimeError("Sopro servisi baslatilamadi (port 7862 timeout)!")

def retire_chatterbox():
    try:
        urllib.request.urlopen(urllib.request.Request(f"{SOPRO_URL}/api/retire", data=b"", method="POST"), timeout=5)
    except Exception:
        pass


def stop_sopro():
    """Stop the Sopro service once the voice is made.

    It holds ~4.7 GB of memory and part of the GPU for the rest of the run,
    where the shot workers need both; ensure_sopro_running starts it again
    for the next film.
    """
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                    # Start-Sopro.ps1 runs sopro_serve.py; matching only
                    # "sopro.server" missed it and left 4.4 GB held all run.
                    "Where-Object { $_.CommandLine -like '*sopro.server*' -or $_.CommandLine -like '*sopro_serve*' -or $_.CommandLine -like '*pocket_serve*' -or $_.CommandLine -like '*chatterbox_serve*' } | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                   capture_output=True, timeout=30)


def prepare_reference(reference_wav_path: str | Path) -> str:
    """Upload reference WAV to Sopro and return reference cache ID."""
    ensure_sopro_running()
    ref_path = Path(reference_wav_path)
    if not ref_path.exists():
        raise FileNotFoundError(f"Referans ses dosyasi bulunamadi: {ref_path}")
        
    # Decode supported media without changing the source reference.
    decoded = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(ref_path), "-t", "30", "-ar", "24000",
         "-ac", "1", "-f", "f32le", "pipe:1"],
        capture_output=True, check=True, timeout=30,
    )
    data, sr = np.frombuffer(decoded.stdout, dtype="<f4"), 24000
    if not len(data) or not np.isfinite(data).all() or np.max(np.abs(data)) < 1e-5:
        raise ValueError("Reference audio is empty, silent or invalid.")
    if len(data.shape) > 1:
        data = data.mean(axis=1)

    # Clamping reference audio to optimal 30 seconds for voice cloning & Sopro buffer safety
    max_ref_samples = min(len(data), int(sr * 30))
    data = data[:max_ref_samples]
    raw_bytes = data.astype("<f4").tobytes()
    
    req = urllib.request.Request(
        f"{SOPRO_URL}/api/reference",
        data=raw_bytes,
        headers={
            "Content-Type": "application/octet-stream",
            "X-Sopro-Sample-Rate": str(sr)
        }
    )
    # 15 s was a quiet machine; under load the reference took longer (TOPIC_6).
    with urllib.request.urlopen(req, timeout=600) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["id"]

def synthesize_text(text: str, reference_id: str, out_wav_path: str | Path,
                    temperature: float = 0.80, top_p: float = 0.90, top_k: int = 25, seed: int = 42,
                    language: str = "en"):
    """Synthesize text using Sopro Turbo GPU engine and save to target WAV."""
    ensure_sopro_running()
    out_path = Path(out_wav_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    clean_text = text.strip()
    payload = {
        "text": clean_text,
        "reference": reference_id,
        "language": language,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "seed": seed
    }
    
    req = urllib.request.Request(
        f"{SOPRO_URL}/api/synthesize",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    from adaptive_governor import get_governor
    governor = get_governor()
    with governor.slot("voice"):
        started = time.perf_counter()
        # Pocket restarts itself between requests past its memory limit; a
        # request that met the restart is sent once more to the new service.
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=900) as resp:
                    raw_pcm = resp.read()
                break
            except (urllib.error.URLError, ConnectionError) as exc:
                if attempt >= 2 or isinstance(exc, urllib.error.HTTPError):
                    governor.observe("voice", time.perf_counter()-started, False, error_type=type(exc).__name__)
                    raise
                ensure_sopro_running()
            except Exception as exc:
                governor.observe("voice", time.perf_counter()-started, False, error_type=type(exc).__name__)
                raise
        governor.observe("voice", time.perf_counter()-started, True)
        
    audio_np = np.frombuffer(raw_pcm, dtype="<f4")
    if not len(audio_np) or not np.isfinite(audio_np).all() or np.max(np.abs(audio_np)) < 1e-5:
        raise ValueError("Sopro returned empty, silent or invalid audio.")
    sample_rate = 24000
    temp_path = out_path.with_suffix(".tmp.wav")
    sf.write(str(temp_path), audio_np, sample_rate)
    temp_path.replace(out_path)
    return out_path
