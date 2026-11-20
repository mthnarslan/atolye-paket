"""How much work this machine can carry right now without hurting it.

The pools used to have a fixed width: sixteen motion decoders, eight
face readers, one browser per 3D shot. A fixed width is only safe on an
empty machine. On a desktop that already carries a browser and an
editor, that width is what turned the screen black, so the width is
read from the memory that is free at the moment the pool is opened and
the workers wait for room when the machine runs low.

There is no new dependency here: psutil is used when it is installed
and the Windows API answers when it is not.
"""

import ctypes
import os
from pathlib import Path
import subprocess
import threading
import time


def _env_int(name, fallback):
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return fallback


# The memory that is left to the desktop, the browser and the editor.
# The pipeline may use the rest, and it waits when even that is gone.
RESERVE_MB = _env_int("DOCUMENTARY_RESERVE_MB", 1200)

# Below this the machine is not allowed to start new heavy work.
CRITICAL_MB = _env_int("DOCUMENTARY_CRITICAL_MB", 700)

# The memory a light media job holds: one frame, or a decode at a
# reduced width. With ffmpeg's default decoder threads (one per core)
# a 1080p H.264 single-frame read held 145 MB; capped at FFMPEG_THREADS
# (below) it holds 56-73 MB (measured 2026-10-26 on a 1080p60 window).
LIGHT_MB = 80

# Decoder threads of each ffmpeg input. A frame-threaded H.264 decoder
# keeps whole frames per thread, so the default (one thread per core,
# 17 here) is what made a decode-only job hold 145-173 MB. Measured on
# a 1080p60 window with the CPU at 100%: a freeze decode 173 -> 57 MB, a
# full decode of a shot 157 -> 55 MB, a single frame 145 -> 61 MB at
# two threads, with the same CPU seconds; a render (decode, scale,
# NVENC) 322 -> 236 MB at four. The decoded pixels do not depend on the
# thread count, so nothing a check or a render sees changes. 0 leaves
# ffmpeg's default.
FFMPEG_THREADS = _env_int("DOCUMENTARY_FFMPEG_THREADS", 2)
FFMPEG_ENCODE_THREADS = _env_int("DOCUMENTARY_FFMPEG_ENCODE_THREADS", 4)
if not 0 < FFMPEG_THREADS <= 4:
    LIGHT_MB = 100  # ffmpeg's own thread count: the old measured cost

# A job's memory shows in the free memory about a second after it
# starts. After this many seconds its charge is no longer counted
# against the free memory a second time (see MemoryGate.budget_mb).
RAMP_SECONDS = 3.0

# How many light jobs may run at the same time. Four left 12 of the 16
# threads idle while a new film's footage fingerprints (~750 windows at
# ~4 s of decode each) held step 3 for over ten minutes.
LIGHT_CEILING = 12

# A hyperframes render (node + headless chrome + libx264 ffmpeg) is outside
# the gate unless it is charged: measured 2026-11-05, the three processes
# together hold 1.1-1.3 GB, and the gate saw none of it while 300 MB encodes
# and 80 MB probes filled the same free memory. install_hyperframes_charge()
# makes each hyperframes governor slot hold this much of MEDIA.
HYPERFRAMES_MB = _env_int("DOCUMENTARY_HYPERFRAMES_MB", 1200)

# A CUDA window read: measured 181 MB working set / 325 MB private for an
# ffmpeg with -hwaccel cuda and scale_cuda (CPU read: 67/63), against the 80
# MB a decode is charged. A read that falls back to the CPU is charged the same.
CUDA_DECODE_MB = _env_int("DOCUMENTARY_CUDA_DECODE_MB", 200)

# A heavy job that has waited this long makes the gate drain: no other job
# is admitted until it runs (so a 1200 MB job can get its room between
# 300 MB encodes), for at most DRAIN_MAX_SECONDS more. Without the cap a
# job that waits on the gate while holding it would stop everything.
DRAIN_SECONDS = _env_int("DOCUMENTARY_GATE_DRAIN_SECONDS", 60)
DRAIN_MAX_SECONDS = _env_int("DOCUMENTARY_GATE_DRAIN_MAX_SECONDS", 180)


def _windows_memory():
    class Status(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = Status()
    status.dwLength = ctypes.sizeof(Status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx failed")
    return status.ullAvailPhys // (1024 * 1024), status.ullTotalPhys // (1024 * 1024)


def memory_mb():
    """Free and total physical memory in megabytes."""
    try:
        import psutil
        virtual = psutil.virtual_memory()
        return int(virtual.available / (1024 * 1024)), int(virtual.total / (1024 * 1024))
    except Exception:
        return _windows_memory()


def free_memory_mb():
    return memory_mb()[0]


def worker_count(requested, per_worker_mb=200, minimum=1, maximum=None):
    """How many workers the free memory allows, never more than asked for.

    A fixed pool width is what made the machine go black. The width is
    a function of the memory that is free now, so the same code is wide
    on an idle machine and narrow on a busy one.
    """
    try:
        wanted = int(requested)
    except (TypeError, ValueError):
        wanted = 0
    if wanted <= 0:
        wanted = maximum or minimum
    limit = os.environ.get("DOCUMENTARY_MAX_WORKERS")
    if limit:
        try:
            wanted = min(wanted, max(1, int(limit)))
        except ValueError:
            pass
    free = free_memory_mb()
    allowed = int((free - RESERVE_MB) // max(1, per_worker_mb))
    allowed = max(minimum, allowed)
    if maximum:
        allowed = min(allowed, maximum)
    return max(minimum, min(wanted, allowed))


def wait_for_room(minimum_mb=CRITICAL_MB, timeout=600):
    """Hold the work until the machine has room again.

    Returns True when there is room, False when the wait ran out. A
    worker that cannot get room stops instead of pushing the machine
    over the edge; the shot is retried by the caller.
    """
    minimum_mb = _env_int("DOCUMENTARY_CRITICAL_MB", minimum_mb)
    deadline = time.time() + timeout
    while True:
        if free_memory_mb() >= minimum_mb:
            return True
        if time.time() >= deadline:
            return False
        time.sleep(2)


class MemoryGate:
    """Admits as many units of work as the free memory allows, right now.

    The width of a pool used to be read once, when the pool opened, and
    it stayed that way for the whole run. A machine that was busy at
    that moment ran on one worker for the rest of the run, and a machine
    that gave memory back half way through stayed narrow. The width is
    read again at every acquisition, so the pool follows the memory
    while the run goes on.

    The budget carries two kinds of job. A heavy job is a 1080p
    encode, a full decode or a concat; it holds the measured 300 MB.
    A light job is a single frame or a decode at a reduced width; it
    holds under 100 MB. They used to wait for the same slot, so a
    queue of probes held the encodes back and the encodes held the
    probes back. Now they cost out of the same budget and a probe
    takes only what is left over: the number of heavy jobs is still
    the number the machine could afford before, and the probes fill
    the gap. The reserve is untouched, so the machine is never taken
    below the level it was taken below before.
    """

    def __init__(self, per_unit_mb, ceiling=None, minimum=1):
        self.per_unit_mb = max(1, int(per_unit_mb))
        self.ceiling = int(ceiling) if ceiling else None
        self.minimum = max(1, int(minimum))
        self._busy = 0
        self._used_mb = 0
        self._light_busy = 0
        # When each running job was admitted, and its charge.
        self._started = {}
        self._lock = threading.Lock()
        # Heavy jobs that are waiting now, by the time they began to wait.
        # While one waits, a light job is admitted only if it leaves the
        # room that heavy job needs; otherwise 80 MB probes refill every
        # gap before 300 MB ever fits (starvation). Light jobs still run
        # whenever the budget is wide, so the memory limit is unchanged.
        self._heavy_waiting = {}  # id(job) -> (began waiting, cost)

    def width(self):
        """How many units the free memory allows at this moment."""
        allowed = int((free_memory_mb() - RESERVE_MB) // self.per_unit_mb)
        allowed = max(self.minimum, allowed)
        if self.ceiling:
            allowed = min(allowed, self.ceiling)
        return allowed

    def _settled_mb(self, now=None):
        """The charges of the jobs that have run long enough to show in the free memory."""
        now = time.monotonic() if now is None else now
        return sum(cost for started, cost in self._started.values() if now - started >= RAMP_SECONDS)

    def budget_mb(self):
        """The memory the media work may hold at this moment.

        The free memory is read now, so a job that has been running for a
        while is already out of it. Its charge used to be subtracted a
        second time through _used_mb, which halved the width of the gate
        once the jobs were running: with 2 GB free and three encodes up,
        the gate saw 2000 - 1200 - 900 and let nothing else in. A job's
        charge is added back once it is RAMP_SECONDS old; a younger job,
        whose memory may not show yet, is still counted by its charge.
        The reserve is still kept free.
        """
        return max(0, free_memory_mb() - RESERVE_MB + self._settled_mb())

    def has_room(self, mb):
        """True when mb more would be admitted now without waiting."""
        with self._lock:
            return self._used_mb + mb <= self.budget_mb()

    def _admit(self, cost, light, token=None):
        with self._lock:
            if self.ceiling and self._busy >= self.ceiling:
                return False
            if light and self._light_busy >= LIGHT_CEILING:
                return False
            if getattr(_HELD, "depth", 0):
                # This thread already holds a gate job: what it starts inside it
                # is covered by that charge. Waiting for room here, while the
                # outer job holds the room, could only deadlock.
                self._busy += 1
                self._used_mb += cost
                if light:
                    self._light_busy += 1
                self._started[token if token is not None else object()] = (time.monotonic(), cost)
                return True
            # One job always runs, even under the reserve: a run that
            # stops entirely delivers nothing. The second one waits.
            budget = self.budget_mb()
            if self._heavy_waiting and not getattr(_HELD, "depth", 0):
                # Drain: the oldest heavy waiter past DRAIN_SECONDS goes first, alone.
                now = time.monotonic()
                oldest = min(self._heavy_waiting.items(), key=lambda kv: kv[1][0])
                age = now - oldest[1][0]
                if DRAIN_SECONDS <= age <= DRAIN_SECONDS + DRAIN_MAX_SECONDS and oldest[0] != id(token):
                    return False
            if light and self._heavy_waiting and self._busy > 0:
                # keep room for the longest-waiting heavy job
                cost_check = cost + self.per_unit_mb
            else:
                cost_check = cost
            if self._used_mb + cost_check <= budget or self._busy == 0:
                self._busy += 1
                self._used_mb += cost
                if light:
                    self._light_busy += 1
                self._started[token if token is not None else object()] = (time.monotonic(), cost)
                return True
            return False

    def _release(self, cost, light, token=None):
        with self._lock:
            self._busy -= 1
            self._used_mb = max(0, self._used_mb - cost)
            if light:
                self._light_busy = max(0, self._light_busy - 1)
            self._started.pop(token, None)

    def heavy(self):
        return _GateJob(self, light=False)

    def heavy_of(self, cost):
        return _GateJob(self, light=False, cost=int(cost))

    def light(self, cost=None):
        return _GateJob(self, light=True, cost=cost)

    def __enter__(self):
        return self.heavy().__enter__()

    def __exit__(self, *exc):
        return False


_WAITED = threading.local()
_INSTALL = {"tries": 0, "done": False}
_HELD = threading.local()  # gate jobs this thread holds: a nested wait is never drained


def waited(reset=True):
    """Seconds this thread's media jobs waited for the gate since the last reset."""
    seconds = getattr(_WAITED, "seconds", 0.0)
    if reset:
        _WAITED.seconds = 0.0
    return seconds


class _GateJob:
    """One job holding a place in the gate's budget."""

    def __init__(self, gate, light, cost=None):
        self.gate = gate
        self.light = light
        self.cost = cost or (LIGHT_MB if light else gate.per_unit_mb)

    def __enter__(self):
        started = time.monotonic()
        gate = self.gate
        if _INSTALL["tries"] < 5 and not _INSTALL["done"]:
            _INSTALL["tries"] += 1  # adaptive_governor may not have been importable when this module loaded
            _INSTALL["done"] = install_hyperframes_charge()
        try:
            while True:
                if gate._admit(self.cost, self.light, self):
                    _WAITED.seconds = getattr(_WAITED, "seconds", 0.0) + time.monotonic() - started
                    _HELD.depth = getattr(_HELD, "depth", 0) + 1
                    return self
                if not self.light:
                    with gate._lock:
                        gate._heavy_waiting.setdefault(id(self), (started, self.cost))
                time.sleep(0.5)
        finally:
            with gate._lock:
                gate._heavy_waiting.pop(id(self), None)

    def __exit__(self, *exc):
        self.gate._release(self.cost, self.light, self)
        _HELD.depth = max(0, getattr(_HELD, "depth", 1) - 1)
        return False


# One media process at a time carries a decoder and an encoder of a
# full frame. Measured on this machine: 312 MB for a 1080p encode and
# under 100 MB for a probe or a single frame. The gate is measured
# against the heavy one, because a run that is too wide is what took
# the screen down. It is the width of the media work that is bounded
# here, not the width of the workers: a worker that waits for a model
# answer holds no memory at all, so the workers may be many while the
# media work stays as narrow as the machine allows.
MEDIA = MemoryGate(per_unit_mb=300, ceiling=12)


def _is_ffmpeg(args):
    return bool(args) and Path(args[0]).stem.lower() == "ffmpeg"


def with_threads(command, threads=None):
    """The ffmpeg command with its first input decoded on at most `threads` threads.

    Left alone: a command that is not ffmpeg, has no input, or already
    sets the threads of its first input, and threads 0.
    """
    args = [str(a) for a in command]
    threads = FFMPEG_THREADS if threads is None else threads
    if threads <= 0 or not _is_ffmpeg(args) or "-i" not in args or "-threads" in args[:args.index("-i")]:
        return args
    return args[:1] + ["-threads", str(int(threads))] + args[1:]


_IMAGE_OUTPUTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def job_kind(command):
    """'heavy', 'decode' or 'copy': what an ffmpeg job holds in memory.

    heavy: it encodes video (a render, a pad, a concat that re-encodes).
    decode: it only decodes, into a null sink, a pipe or still images
    (freeze, black and decode checks, review frames, a subtitle band).
    copy: it copies the video stream (an audio mux, a stream-copy concat).
    Anything not recognised is heavy, as every job was before.
    """
    args = [str(a) for a in command]
    if not _is_ffmpeg(args):
        return "heavy"
    video_codec = None
    for i, a in enumerate(args[:-1]):
        if a in ("-c:v", "-vcodec", "-c", "-codec", "-codec:v"):
            video_codec = args[i + 1]
    if video_codec == "copy":
        return "copy"
    if video_codec is not None:
        return "heavy"
    output = args[-1].lower()
    formats = [args[i + 1] for i, a in enumerate(args[:-1]) if a == "-f" and i > args.index("-i")] if "-i" in args else []
    if output == "-" or "null" in formats or "rawvideo" in formats or output.endswith(_IMAGE_OUTPUTS):
        return "decode"
    return "heavy"


# What a stream-copy job holds: an audio mux with the video copied, 27-33 MB.
COPY_MB = 60


def media_run(command, timeout=150, **kwargs):
    """Run a media subprocess while it holds a memory slot.

    The slot is the job's measured cost (job_kind): the generic runner
    charged every job as an encode, so a single-frame read or an audio
    mux of a shot (30-70 MB) waited for 300 MB of room.
    """
    kwargs.setdefault("capture_output", True)
    kind = job_kind(command)
    if kind == "heavy":
        with MEDIA.heavy():
            return subprocess.run(with_threads(command, FFMPEG_ENCODE_THREADS), timeout=timeout, **kwargs)
    with MEDIA.light(DECODE_MB if kind == "decode" else COPY_MB):
        return subprocess.run(with_threads(command), timeout=timeout, **kwargs)


# A full-resolution decode with no encode: 149 MB measured for a 1080p
# freeze scan with ffmpeg's default threads, 49-73 MB at FFMPEG_THREADS.
# Charged as a heavy job, the freeze check of a shot waited a median 15 s
# for one of the two slots 1.9 GB of free memory allowed, and ran in 0.8 s.
DECODE_MB = 80 if 0 < FFMPEG_THREADS <= 4 else 150


def _decode_cost(cpu_cost, cuda):
    """The charge of a decode: a CUDA read holds more than a CPU one (see CUDA_DECODE_MB)."""
    if cuda and GPU_DECODE and _GPU_STATE["failures"] < GPU_DECODE_MAX_FAILURES:
        return max(CUDA_DECODE_MB, cpu_cost or 0)
    return cpu_cost


def decode_run(command, timeout=150, cuda=False, **kwargs):
    """Run a decode-only media subprocess at its measured memory cost.

    cuda=True decodes on the GPU when it can (see _cuda_command); cuda="exact"
    decodes on the GPU and converts on the CPU, so the pixels are the CPU
    decode's own (see _cuda_exact_command)."""
    kwargs.setdefault("capture_output", True)
    return _run_light(command, DECODE_MB, timeout, cuda, kwargs)


def probe_run(command, timeout=150, cuda=False, **kwargs):
    """Run a cheap media subprocess while it holds a light memory slot.

    cuda=True decodes on the GPU when it can (see _cuda_command); cuda="exact"
    keeps the CPU decode's pixels (see _cuda_exact_command)."""
    kwargs.setdefault("capture_output", True)
    return _run_light(command, None, timeout, cuda, kwargs)


def _run_light(command, cpu_cost, timeout, cuda, kwargs, gpu_command=None):
    """One light media job. The GPU slot is taken first (without waiting), so the job is
    charged CUDA_DECODE_MB only when it really runs on the GPU: a read that finds the
    slots taken used to be charged 200 MB for its CPU run and waited for room it did not need."""
    command = with_threads(command)
    gpu = gpu_command
    if gpu is None and cuda:
        gpu = _cuda_exact_command(command) if cuda == "exact" else _cuda_command(command)
    state = _EXACT_STATE if (gpu_command is not None or cuda == "exact") else _GPU_STATE
    slot = bool(gpu) and GPU_DECODE and state["failures"] < GPU_DECODE_MAX_FAILURES and _GPU_SLOTS.acquire(blocking=False)
    try:
        with MEDIA.light(max(CUDA_DECODE_MB, cpu_cost or 0) if slot else cpu_cost):
            if slot:
                try:
                    proc = subprocess.run(gpu, timeout=timeout, **kwargs)
                    if proc.returncode == 0:
                        state["failures"] = 0
                        return proc
                except (OSError, subprocess.SubprocessError):
                    pass
                state["failures"] += 1
            return subprocess.run(command, timeout=timeout, **kwargs)
    finally:
        if slot:
            _GPU_SLOTS.release()


# Window reads on the GPU: an ffmpeg decode with -hwaccel cuda and the
# scaling in scale_cuda. Measured on 20 windows (1 fps over 30 s, 640x360):
# CPU 258 s of CPU time in 51.7 s, CUDA 21 s of CPU time in 33.4 s. A single
# frame read gains nothing (50.2 s against 51.2 s), so only the window reads
# ask for it. Each CUDA ffmpeg holds about 190 MB of the 4 GB card that
# SigLIP and the encodes share, so at most GPU_DECODE_SLOTS run at once and
# a read that finds them taken runs on the CPU instead of waiting.
GPU_DECODE = os.environ.get("DOCUMENTARY_GPU_DECODE", "1") != "0"
GPU_DECODE_SLOTS = 3
_GPU_SLOTS = globals().get("_GPU_SLOTS") or threading.BoundedSemaphore(GPU_DECODE_SLOTS)
# After this many CUDA failures in a row (no card, no driver) the process
# stops trying; a success resets the count.
GPU_DECODE_MAX_FAILURES = 20
_GPU_STATE = globals().get("_GPU_STATE") or {"failures": 0}
_SCALE_INTERP = {"bicubic": "bicubic", "bilinear": "bilinear", "lanczos": "lanczos", "neighbor": "nearest"}


def _cuda_chain(chain):
    """The -vf chain for CUDA frames: the first scale (after any fps) on the GPU, then download."""
    parts = chain.split(",")
    for n, part in enumerate(parts):
        name, _, value = part.partition("=")
        if name == "fps":
            continue
        if name == "scale":
            opts = value.split(":")
            extra = []
            for opt in opts[2:]:
                key, _, val = opt.partition("=")
                if key != "flags" or val not in _SCALE_INTERP:
                    break
                extra.append("interp_algo=" + _SCALE_INTERP[val])
            else:
                if len(opts) >= 2 and "=" not in opts[0] + opts[1]:
                    # nv12 needs even sides: -1 becomes -2.
                    w, h = ("-2" if s == "-1" else s for s in opts[:2])
                    parts[n] = "scale_cuda=%s" % ":".join([w, h] + extra + ["format=nv12"]) + ",hwdownload,format=nv12"
                    return ",".join(parts)
        break
    return "hwdownload,format=nv12," + chain


def _cuda_command(command):
    """The ffmpeg command decoding on the GPU, or None when it cannot be rewritten."""
    args = [str(a) for a in command]
    if not args or Path(args[0]).stem.lower() != "ffmpeg" or "-i" not in args or "-hwaccel" in args:
        return None
    if "-vf" in args:
        k = args.index("-vf") + 1
        args[k] = _cuda_chain(args[k])
    elif "-filter_complex" in args:
        k = args.index("-filter_complex") + 1
        if not args[k].startswith("[0:v]"):
            return None
        args[k] = "[0:v]hwdownload,format=nv12," + args[k][len("[0:v]"):]
    else:
        return None
    return args[:1] + ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"] + args[1:]


_EXACT_STATE = globals().get("_EXACT_STATE") or {"failures": 0}
_EXACT_PRE = ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
_EXACT_DOWNLOAD = "hwdownload,format=nv12,format=yuv420p"
_FRAME_FILTERS = ("fps", "select")  # run on GPU frames as they are


def _split_filters(chain):
    """A -vf chain cut at its top level commas (not those inside quotes or after a backslash)."""
    parts, cur, quote, i = [], [], False, 0
    while i < len(chain):
        ch = chain[i]
        if ch == "\\" and i + 1 < len(chain):
            cur.append(chain[i:i + 2])
            i += 2
            continue
        if ch == "'":
            quote = not quote
        if ch == "," and not quote:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return parts


def _exact_chain(chain):
    """The -vf chain with the decoded frames downloaded after its leading fps/select filters:
    the GPU decodes and drops frames, the CPU does everything else on the same pixels."""
    parts = _split_filters(chain)
    n = 0
    while n < len(parts) and parts[n].partition("=")[0] in _FRAME_FILTERS:
        n += 1
    return ",".join(parts[:n] + [_EXACT_DOWNLOAD] + parts[n:])


def _cuda_exact_command(command):
    """The one-input ffmpeg command decoding on the GPU and giving the CPU decode's pixels, or None.

    NVDEC and the software H.264 decoder produce the same 8-bit 4:2:0 frames, the download
    gives them back as NV12, and the CPU filters see what they saw before. Measured byte-identical
    on single frames, select boards, window scans and review frames (R_ffmpeg_cpu). Anything
    that is not 8-bit 4:2:0 fails the download and the caller runs the CPU command."""
    args = [str(a) for a in command]
    if not args or Path(args[0]).stem.lower() != "ffmpeg" or args.count("-i") != 1 or "-hwaccel" in args or "-vf" not in args:
        return None
    k = args.index("-vf") + 1
    args[k] = _exact_chain(args[k])
    return args[:1] + _EXACT_PRE + args[1:]


def grab_frames(path, items, width=640, timeout=60):
    """Write one still per (seconds, output) of one file in a single ffmpeg process.

    The command of sources.sample for each item (-ss seek, scale to width, yuvj420p) with the
    inputs side by side, so a window read for its three contact frames costs one process
    start and one CUDA context instead of three. Raises RuntimeError on any failure.
    """
    items = [(max(0, float(t)), str(o)) for t, o in items]
    if not items:
        return

    def build(pre, chain):
        cmd = ["ffmpeg", "-v", "error", "-xerror", "-y"]
        for t, _ in items:
            cmd += [*pre, "-threads", str(FFMPEG_THREADS or 2), "-ss", str(t), "-i", str(path)]
        for i, (_, out) in enumerate(items):
            cmd += ["-map", "%d:v:0" % i, "-frames:v", "1", "-vf", chain, "-pix_fmt", "yuvj420p", out]
        return cmd

    chain = "scale=%d:-1" % width
    proc = _run_light(build([], chain), DECODE_MB, timeout, False, {"capture_output": True},
                      gpu_command=build(_EXACT_PRE, _EXACT_DOWNLOAD + "," + chain))
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[-2200:])


def _decode(command, timeout, cuda, kwargs):
    """Run the command, on the GPU first when asked and a slot is free; the CPU command on any failure."""
    command = [str(a) for a in command]
    gpu = _cuda_command(command) if cuda and GPU_DECODE and _GPU_STATE["failures"] < GPU_DECODE_MAX_FAILURES else None
    if gpu and _GPU_SLOTS.acquire(blocking=False):
        try:
            proc = subprocess.run(gpu, timeout=timeout, **kwargs)
            if proc.returncode == 0:
                _GPU_STATE["failures"] = 0
                return proc
        except (OSError, subprocess.SubprocessError):
            pass
        finally:
            _GPU_SLOTS.release()
        _GPU_STATE["failures"] += 1
    return subprocess.run(command, timeout=timeout, **kwargs)


def install_hyperframes_charge():
    """Make every governor slot("hyperframes") also hold HYPERFRAMES_MB of MEDIA.

    cards.py, motion.py and three_render.py take that slot around the
    hyperframes render; they stay as they are (they are in the shot
    identity). The governor slot is taken first, the gate second, and both
    are released together. Called once; True when installed.
    """
    try:
        from contextlib import contextmanager
        import adaptive_governor
        gov = adaptive_governor.get_governor()
    except Exception:
        return False
    if getattr(gov, "_media_charged", False):
        return True
    if HYPERFRAMES_MB <= 0:
        return False
    original = gov.slot

    @contextmanager
    def slot(channel, cancel=None):
        with original(channel, cancel):
            if channel != "hyperframes":
                yield
                return
            with MEDIA.heavy_of(HYPERFRAMES_MB):
                yield

    gov.slot = slot
    gov._media_charged = True
    return True


_INSTALL["done"] = install_hyperframes_charge()


# HyperFrames encodes its capture with libx264 (preset medium) in an ffmpeg
# of its own, which held 892 MB working set; the same encode with -threads 4
# holds 463 MB (2026-11-05, 1080p). HyperFrames reads the path of that ffmpeg
# from HYPERFRAMES_FFMPEG_PATH; the shim there adds "-threads N" after
# "-c:v libx264" and runs the real ffmpeg for everything else. cards.py and
# motion.py (shot identity) stay as they are: only this process's
# environment changes, and the subprocess they start inherits it.
HF_SHIM = os.environ.get("DOCUMENTARY_HF_SHIM", "C:/Users/meteh/Kanallar/bin/hf_ffmpeg_shim.exe")


def use_hyperframes_encoder_threads():
    """Point HyperFrames at the thread-capping ffmpeg shim; True when set."""
    import shutil
    if os.environ.get("DOCUMENTARY_HF_THREADS", "4") in ("0", "") or "HYPERFRAMES_FFMPEG_PATH" in os.environ:
        return False
    real = shutil.which("ffmpeg")
    if not real or not Path(HF_SHIM).is_file():
        return False
    os.environ["HF_REAL_FFMPEG"] = real
    os.environ["HF_X264_THREADS"] = os.environ.get("DOCUMENTARY_HF_THREADS", "4")
    os.environ["HYPERFRAMES_FFMPEG_PATH"] = HF_SHIM
    return True


use_hyperframes_encoder_threads()
