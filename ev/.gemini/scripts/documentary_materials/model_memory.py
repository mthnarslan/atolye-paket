"""Memory trims for the loaded image-text model that keep every score bit for bit.

The SigLIP 2 model of picture_fit has 375M parameters, and 197M of them
are the text token table (256000 x 768): 786 MB of the 1.6 GB it holds
in RAM when the card is full and it runs on the CPU, and 393 MB of video
memory when it runs half precision on the card. A sentence of at most 64
tokens reads 64 rows of it. The table is written once to a file in the
dtype the model holds it in, and the lookup reads those rows from a
memory map: the same bytes, so every text vector and every fit is the
same as before (tests/test_model_memory.py), while the rows not read
stay on disk and the rows read are file-backed pages, not commit.

This lives outside picture_fit on purpose: picture_fit.py is part of
every VIDEO shot identity, and this changes no output. Set
DOCUMENTARY_SLIM_SIGLIP=0 to keep the table in memory.
"""
import hashlib
import os
import tempfile
import threading
from pathlib import Path

CACHE = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "documentary_materials"


def enabled():
    return os.environ.get("DOCUMENTARY_SLIM_SIGLIP", "1") != "0"


def _numpy_dtype(dtype):
    import numpy as np
    import torch
    return {torch.float32: np.float32, torch.float16: np.float16}.get(dtype)


def _table_path(weight):
    """A file named by the table's shape, dtype and a sample of its bytes."""
    import numpy as np
    rows = weight.detach()[:: max(1, weight.shape[0] // 64)].cpu().numpy()
    tag = hashlib.sha1(np.ascontiguousarray(rows).tobytes()).hexdigest()[:16]
    return CACHE / ("token_table_%dx%d_%s_%s.bin" % (weight.shape[0], weight.shape[1],
                                                     str(weight.dtype).replace("torch.", ""), tag))


def _write_table(weight, path):
    if path.is_file() and path.stat().st_size == weight.numel() * weight.element_size():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part%d" % os.getpid())
    weight.detach().cpu().contiguous().numpy().tofile(part)
    os.replace(part, path)


def _mapped_embedding(path, shape, dtype, device):
    import numpy as np
    import torch

    class MappedEmbedding(torch.nn.Module):
        """nn.Embedding whose table is read from a memory-mapped file."""

        def __init__(self):
            super().__init__()
            self.device = device
            self.table = np.memmap(path, dtype=_numpy_dtype(dtype), mode="r", shape=tuple(shape))

        def forward(self, ids):
            return torch.from_numpy(np.ascontiguousarray(self.table[ids.cpu().numpy()])).to(self.device)

    return MappedEmbedding()


def slim_text_table(model, lock=None):
    """Replace model.text.token_embedding by a memory-mapped copy; True when done.

    Only a plain float32/float16 nn.Embedding is replaced: its forward is
    a pure row lookup. The copy is checked against the table before it
    takes over.
    """
    import torch
    text = getattr(model, "text", None)
    emb = getattr(text, "token_embedding", None)
    if (not isinstance(emb, torch.nn.Embedding) or emb.max_norm is not None
            or emb.weight.dim() != 2 or _numpy_dtype(emb.weight.dtype) is None):
        return False
    weight = emb.weight
    path = _table_path(weight)
    _write_table(weight, path)
    mapped = _mapped_embedding(path, weight.shape, weight.dtype, weight.device)
    probe = torch.arange(0, weight.shape[0], max(1, weight.shape[0] // 997), device=weight.device)
    with torch.no_grad():
        if not torch.equal(mapped(probe), emb(probe)):
            return False
    with (lock or threading.Lock()):
        text.token_embedding = mapped
    on_card = weight.device.type == "cuda"
    del emb, weight
    if on_card:
        torch.cuda.empty_cache()
    return True


def slim_picture_fit():
    """Wait for picture_fit's model in the background and slim its token table once."""
    def run():
        try:
            from . import picture_fit as pf
            state = pf._model()
            if state is not None and not pf._STATE.get("slim"):
                pf._STATE["slim"] = slim_text_table(state[0], pf._STATE["run"])
            watch_picture_fit_idle()
        except Exception:
            pass  # the model keeps its own table
    if not enabled():
        return None
    thread = threading.Thread(target=run, name="picture-fit-slim", daemon=True)
    thread.start()
    return thread


# The GPU voice engine (Chatterbox, port 7864) needs about 3.4 GB of the
# 4 GB card. picture_fit takes the card when it loads while the voice
# service happens to be down, and then the voice spills into shared memory:
# measured 2026-11-05, 2714 MB dedicated + 726 MB shared, 1 token/s instead
# of ~25. While the voice service listens, the model runs on the CPU, as it
# already does whenever the card is full at load time.
VOICE_GPU_PORT = int(os.environ.get("DOCUMENTARY_VOICE_GPU_PORT", "7864"))


def _voice_gpu_up():
    import socket
    try:
        with socket.create_connection(("127.0.0.1", VOICE_GPU_PORT), timeout=1):
            return True
    except OSError:
        return False


def release_picture_fit_gpu():
    """Move picture_fit's model off the card when the GPU voice service is up; True when moved."""
    try:
        import sys
        pf = sys.modules.get(__package__ + ".picture_fit")
        state = pf and pf._STATE.get("model")
        if not state or state[3] != "cuda" or not _voice_gpu_up():
            return False
        import torch
        model, preprocess, tokenizer, _ = state
        with pf._STATE["load"], pf._STATE["run"]:
            model = model.float().to("cpu")
            text = getattr(model, "text", None)
            emb = getattr(text, "token_embedding", None)
            if emb is not None and hasattr(emb, "table"):
                emb.device = "cpu"

                class _AsFloat(torch.nn.Module):
                    def __init__(self, inner):
                        super().__init__()
                        self.inner = inner

                    def forward(self, ids):
                        return self.inner(ids).float()

                text.token_embedding = _AsFloat(emb)
            pf._STATE["model"] = (model, preprocess, tokenizer, "cpu")
            torch.cuda.empty_cache()
        return True
    except Exception:
        return False


threading.Thread(target=release_picture_fit_gpu, name="picture-fit-gpu-release", daemon=True).start()


# --- darbogaz_1107/G_ram: give the model back when stage 3 is not using it ------------------------
# The bridge process lives for the whole batch, so the model (about 0.7 GB on the CPU after the
# token-table trim, 0.4 GB of video memory on the card) and the torch/CUDA runtime pages stay in
# RAM while stages 1, 2 and 4 of the other films run. The model is dropped after IDLE seconds
# without an embedding; picture_fit._model() loads it again on the next use (preload() at the
# start of stage 3 does that while the sources download). No score changes: same weights, same code.
# Default off (2026-11-15, S14): on Windows a dropped model's pages do not come back to the OS, so each
# reload stacked another copy (+4.4 GB over a batch). Set the variable to a positive number to re-enable.
IDLE_RELEASE_SECONDS = float(os.environ.get("DOCUMENTARY_SIGLIP_IDLE_RELEASE_S", "0"))
_LAST_USE = {"t": 0.0}


def _trim_working_set():
    """Ask Windows to move this process's idle pages to standby (they come back on a touch)."""
    try:
        import ctypes
        ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
    except Exception:
        pass


def release_picture_fit_model():
    """Drop picture_fit's model, free the card and trim the working set; True when a model was dropped."""
    import sys, gc, time
    pf = sys.modules.get((__package__ or "") + ".picture_fit") or sys.modules.get("picture_fit")
    if pf is None or pf._STATE.get("model") is None:
        return False
    # Wait for a running embedding (the same lock _embed takes), never interrupt one.
    with pf._STATE["load"], pf._STATE["run"]:
        if time.time() - _LAST_USE["t"] < IDLE_RELEASE_SECONDS:
            return False
        pf._STATE["model"] = None
        pf._STATE["slim"] = False
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    _trim_working_set()
    return True


def watch_picture_fit_idle():
    """Stamp every embedding and release the model after IDLE_RELEASE_SECONDS without one."""
    if IDLE_RELEASE_SECONDS <= 0:
        return None
    import sys, time
    pf = sys.modules.get((__package__ or "") + ".picture_fit") or sys.modules.get("picture_fit")
    if pf is None or getattr(pf, "_idle_watch", False):
        return None
    original = pf._embed

    def stamped(frames):
        _LAST_USE["t"] = time.time()
        try:
            return original(frames)
        finally:
            _LAST_USE["t"] = time.time()

    pf._embed = stamped
    load = pf._model

    def stamped_model():
        _LAST_USE["t"] = time.time()    # a caller that just asked for the model is about to embed
        return load()

    pf._model = stamped_model
    pf._idle_watch = True
    _LAST_USE["t"] = time.time()

    def loop():
        while True:
            time.sleep(30)
            try:
                if time.time() - _LAST_USE["t"] > IDLE_RELEASE_SECONDS:
                    release_picture_fit_model()
                elif pf._STATE.get("model") is not None and not pf._STATE.get("slim") and enabled():
                    # reloaded after a release: slim the token table again
                    pf._STATE["slim"] = slim_text_table(pf._STATE["model"][0], pf._STATE["run"])
            except Exception:
                pass
    t = threading.Thread(target=loop, name="picture-fit-idle-release", daemon=True)
    t.start()
    return t
