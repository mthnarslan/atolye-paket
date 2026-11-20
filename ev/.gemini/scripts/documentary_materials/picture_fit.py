"""How well the opening seconds of a video range fit the shot's sentence.

About a third of the selector's picks came back from the review as FAIL:
the frames showed another subject than the sentence. Each of those cost
a render and a review. An image-text model (SigLIP 2) compares the shot
text (story_plan.visual_goal and the narration) with the frames of the
first four seconds of the range, minus a penalty for frames that look
more like a title card, an anchor, a document, a flag, a map or a logo.

Measured on the 179 reviewed VIDEO picks of the Gotthard run, a fit
below VETO caught 23 of the 49 FAIL picks and wrongly refused 1 of the
40 PASS and 10 of the 90 PARTIAL picks. On the 156 reviewed picks of
the Kailasa run, which the threshold was not chosen on, it caught 14 of
31 FAIL and refused 0 of 44 PASS and 5 of 81 PARTIAL. The negative
prompts, the penalty and the threshold are the measured ones; changing
any of them moves the threshold.

Nothing here is required. A machine without open_clip or the model, a
card that is full, any error, or DOCUMENTARY_SIGLIP=0 returns None, and
the caller behaves as it did without the model.

The state survives a reload of the package: the bridge reloads the
material modules before every stage request, a reload re-executes the
module in its own namespace, and the model would be loaded again.
"""
import os
import string
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import resources
from .sources import local_time

MODEL = "ViT-B-16-SigLIP2"
PRETRAINED = "webli"
TOKENIZER = "timm/ViT-B-16-SigLIP2"

NEGATIVE = ("a title card with text", "a news anchor talking to the camera",
            "a document page", "a flag", "a map", "a logo on a plain background")
PENALTY = 0.5
VETO = -0.01
# A BBC library window (bbc_library) was already found by its fit to the
# sentence, so the veto line lets nearly all of them through. On the 63
# reviewed library picks of TOPIC_1 the fit separates the review's PASS
# from its rejects (AUC 0.77, medians 0.067 vs 0.035); a floor at 0.02
# refuses 8 of 25 rejects and 5 of 38 passes (0.035: 12/25 and 7/38,
# 0.009: 7/25 and 4/38). Library windows only; the others keep VETO.
LIBRARY_FLOOR = 0.02


def floor(assets):
    """The lowest fit the assets may play at: LIBRARY_FLOOR when any is a library window."""
    return LIBRARY_FLOOR if any(a.get("library") for a in assets) else VETO

# The review sees the opening of the shot first. Four frames spread over
# the first four seconds decide as well as all eight read at 2 per second
# (24 of 49 FAIL, 1 of 40 PASS, 9 of 90 PARTIAL on Gotthard).
SECONDS = 4.0
FRAMES = 4
_SIDE = 224
GPU_FREE_MB = 1500

_STATE = globals().get("_STATE") or {
    "model": None, "failed": False, "load": threading.Lock(), "run": threading.Lock(),
    "cache": threading.Lock(), "ranges": {}, "pending": {}, "texts": {}}


def enabled():
    return os.environ.get("DOCUMENTARY_SIGLIP", "1") != "0" and not _STATE["failed"]


def _model():
    """The model, loaded once per process; None when it cannot load."""
    with _STATE["load"]:
        if _STATE["model"] is not None or _STATE["failed"]:
            return _STATE["model"]
        try:
            import torch
            import open_clip
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
            # open_clip's own tokenizer for this model goes through the
            # transformers package, which is broken on this machine.
            try:
                vocab = hf_hub_download(TOKENIZER, "tokenizer.json", local_files_only=True)
            except Exception:
                vocab = hf_hub_download(TOKENIZER, "tokenizer.json")
            tokenizer = Tokenizer.from_file(vocab)
            tokenizer.enable_truncation(64)
            tokenizer.enable_padding(length=64, pad_id=tokenizer.token_to_id("<pad>"))
            model, _, preprocess = open_clip.create_model_and_transforms(MODEL, pretrained=PRETRAINED)
            model.eval()
            device = "cpu"
            # The 4 GB card is shared with the renders; the half-precision
            # model takes about 1 GB at its peak, and a card without that
            # much free is left alone: four frames a shot are cheap on the CPU.
            if torch.cuda.is_available():
                try:
                    if torch.cuda.mem_get_info()[0] >= GPU_FREE_MB * 2**20:
                        model = model.half().to("cuda")
                        device = "cuda"
                except Exception:  # the card is shared and may be full
                    model = model.float().to("cpu")
                    torch.cuda.empty_cache()
            _STATE["model"] = (model, preprocess, tokenizer, device)
        except Exception:
            _STATE["failed"] = True
        return _STATE["model"]


def _unit(rows):
    return rows / rows.norm(dim=-1, keepdim=True)


def _texts(texts):
    """The unit vectors of the texts, as a float tensor on the CPU."""
    import torch
    missing = [t for t in dict.fromkeys(texts) if t not in _STATE["texts"]]
    if missing:
        model, _, tokenizer, device = _STATE["model"]
        # The model was trained on lowercase text without punctuation.
        clean = [" ".join(t.replace("_", " ").translate(str.maketrans("", "", string.punctuation)).lower().split())
                 for t in missing]
        ids = torch.tensor([e.ids for e in tokenizer.encode_batch(clean)], device=device)
        with _STATE["run"], torch.no_grad():
            rows = _unit(model.encode_text(ids).float().cpu())
        _STATE["texts"].update(zip(missing, rows))
    return torch.stack([_STATE["texts"][t] for t in texts])


def _key(asset):
    path = asset.get("path")
    start, end = float(asset.get("start", 0)), float(asset.get("end", 0))
    if not path or end <= start or not Path(path).is_file():
        return None
    return (str(path), round(start, 2), round(end, 2))


def _frames(key):
    """The PIL frames of the first seconds of the range, read in one pass."""
    from PIL import Image
    path, start, end = key
    span = min(SECONDS, end - start)
    proc = resources.probe_run(
        ["ffmpeg", "-hide_banner", "-nostats", "-v", "error",
         "-ss", str(local_time(path, start)), "-t", str(span + 0.05), "-i", path,
         "-vf", f"fps=2,scale={_SIDE}:{_SIDE}:flags=bicubic", "-an",
         "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
        capture_output=True, timeout=60, cuda=True)
    size = _SIDE * _SIDE * 3
    data = proc.stdout or b""
    frames = [Image.frombytes("RGB", (_SIDE, _SIDE), data[i:i + size])
              for i in range(0, len(data) - size + 1, size)]
    if len(frames) > FRAMES:
        last = len(frames) - 1
        frames = [frames[round(i * last / (FRAMES - 1))] for i in range(FRAMES)]
    return frames


def _embed(frames):
    import torch
    model, preprocess, _, device = _STATE["model"]
    batch = torch.stack([preprocess(f) for f in frames]).to(device)
    with _STATE["run"], torch.no_grad():
        return _unit(model.encode_image(batch.half() if device == "cuda" else batch).float().cpu())


def _range_vectors(keys):
    """The frame vectors of every range, read once per (path, start, end).

    The shots of a run share their pool and run at the same time, so a
    range that another thread is reading is waited for, not read again.
    """
    keys = [k for k in dict.fromkeys(keys) if k]
    own, wait = [], []
    with _STATE["cache"]:
        for key in keys:
            if key in _STATE["ranges"]:
                continue
            if key in _STATE["pending"]:
                wait.append(_STATE["pending"][key])
            else:
                _STATE["pending"][key] = threading.Event()
                own.append(key)
    try:
        if own:
            def read(key):
                try:
                    return _frames(key)
                except Exception:
                    return []
            with ThreadPoolExecutor(max_workers=min(6, len(own))) as pool:
                for key, frames in zip(own, pool.map(read, own)):
                    try:
                        vectors = _embed(frames) if frames else None
                    except Exception:
                        vectors = None
                    # Each range is released as soon as it is read: a shot
                    # waiting for one range does not wait for the whole pool.
                    with _STATE["cache"]:
                        _STATE["ranges"][key] = vectors
                        _STATE["pending"].pop(key).set()
    finally:
        with _STATE["cache"]:
            for key in own:
                if key in _STATE["pending"]:
                    _STATE["ranges"].setdefault(key, None)
                    _STATE["pending"].pop(key).set()
    for event in wait:
        event.wait(120)
    return {k: _STATE["ranges"].get(k) for k in keys}


def shot_text(shot):
    plan = shot.get("story_plan") if isinstance(shot.get("story_plan"), dict) else {}
    return ". ".join(str(p).strip().rstrip(".") for p in (plan.get("visual_goal"), shot.get("narration")) if p)


def scores(shot, assets, read=True):
    """The fit of each asset's opening seconds to the shot, by asset id.

    An asset whose frames cannot be read is missing from the result.
    None means the model is off, could not load or failed, or, without
    read, that the background read of the catalog is still running: the
    caller does not wait minutes for an order it can do without.
    """
    if not enabled() or not assets or (not read and _STATE.get("warming")):
        return None
    try:
        if _model() is None:
            return None
        text = shot_text(shot)
        if not text:
            return None
        keys = {a["id"]: _key(a) for a in assets}
        vectors = _range_vectors(keys.values())
        texts = _texts([text] + list(NEGATIVE))
        result = {}
        for cid, key in keys.items():
            rows = vectors.get(key) if key else None
            if rows is None:
                continue
            sims = rows @ texts.T
            result[cid] = float((sims[:, 0] - PENALTY * sims[:, 1:].max(dim=1).values).mean())
        return result
    except Exception:
        return None


def fit(shot, segments):
    """The fit of the segments a shot plays, averaged, or None when unknown."""
    found = scores(shot, [{**s, "id": i} for i, s in enumerate(segments)])
    if not found:
        return None
    return sum(found.values()) / len(found)


def shows_person(frame_bgr):
    """False when the frame reads as an animal or a landscape, not a person.

    The face detector fires on what is not a person: on the Siberian taiga
    film a tiger's face covered 2.5-3.2 percent of the frame at 0.78
    confidence, over the film's 2 percent line, and snowy forest footage
    was flagged too, so good shots were thrown out as a person talking to
    the camera. None when the model is unavailable, so the detector's
    answer stands.
    """
    if not enabled() or _model() is None:
        return None
    from PIL import Image
    image = Image.fromarray(frame_bgr[:, :, ::-1].copy())
    person, animal, landscape = (_texts(["a photo of a person", "a photo of an animal", "a photo of a landscape"])
                                 @ _embed([image])[0]).tolist()
    return person >= max(animal, landscape)


def preload():
    """Load the model in the background while the sources download.

    Loaded on first use it held the first vetoes for 70-110 s after the
    shot queue started.
    """
    if enabled():
        threading.Thread(target=_model, name="picture-fit-load", daemon=True).start()


def warm(assets):
    """Load the model and read the ranges in the background.

    Reading the opening frames of a catalog of about 150 windows took
    about three minutes on a busy machine. A shot that waited for that
    would hold its worker, so the run reads them here while the first
    shots are selected, and the shot list is ordered once they are in.
    """
    def read():
        try:
            # A few ranges at a time, so a shot that needs a range the
            # warm-up has not reached reads it itself instead of waiting.
            keys = [_key(a) for a in assets]
            # Two at a time: the warm-up is background work and must leave
            # the media slots to the shot workers.
            for i in range(0, len(keys) if _model() is not None else 0, 2):
                _range_vectors(keys[i:i + 2])
        except Exception:
            pass  # the shots read what they need themselves
        finally:
            _STATE["warming"] = False
    if not enabled():
        return None
    _STATE["warming"] = True
    thread = threading.Thread(target=read, name="picture-fit-warm", daemon=True)
    thread.start()
    return thread
