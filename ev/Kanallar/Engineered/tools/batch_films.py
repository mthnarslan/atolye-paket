"""Produce the TOPIC_2..9 wildlife films one after another, then free their disk.

For each film: a clean film folder (narration + reference voice + wildlife
profile), stages 1-4 through the bridge, up to four more stage 3-4 runs when
the material is blocked (approved shots are kept between runs), the delivery
ZIP copied to C:\\Users\\meteh\\Belgesel_Teslim as NN_<title>.zip, and the run's
own work folders deleted. A film that still fails is logged and left in place.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SRC = Path(r"C:\Users\meteh\Downloads\Compressed\drive-download-20261025T064810Z-1-001")
FILMS = Path(r"C:\Users\meteh\Films")
OUT = Path(r"C:\Users\meteh\Belgesel_Teslim")
CODEX = Path(r"C:\Users\meteh\CodexOutputs")
ENGINEERED = Path(r"C:\Users\meteh\OneDrive\Desktop\Channells\ENGINEERED")
DRIVE = Path(__file__).with_name("drive.py")
LOG = OUT / "batch.log"


def log(msg):
    OUT.mkdir(parents=True, exist_ok=True)
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def bridge_up(wait=600):
    import urllib.request
    end = time.time() + wait
    while time.time() < end:
        try:
            urllib.request.urlopen("http://127.0.0.1:8099/", timeout=5)
            return True
        except Exception as exc:
            if "HTTP Error" in str(exc):
                return True
        time.sleep(15)
    return False


def drive(folder, start, end):
    # A bridge restart must not burn the retries in one second (TOPIC_2,
    # 13:32): wait for it to answer, and pause between attempts.
    bridge_up()
    time.sleep(20)
    t = time.time()
    p = subprocess.run([sys.executable, str(DRIVE), str(folder), str(start), str(end), "wildlife"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = (p.stdout or "")[-1500:]
    log("  drive %d-%d rc=%d in %.0f min: %s" % (start, end, p.returncode, (time.time() - t) / 60,
                                                tail.replace("\n", " | ")[-600:]))
    return p.returncode, tail


VOICE_LOCK = OUT / "voice.lock"


def voice_then_rest(folder):
    """Stage 1-2 one film at a time, then stage 3-4 alongside the others.

    The voice service (Sopro, port 7862) serves one film: a second film's
    stage 1 timed out in 15 s three times while another was voiced
    (TOPIC_6 and TOPIC_9, 2026-10-26). It holds ~3.7 GB, so it is stopped
    when no other lane waits for it.
    """
    # Pocket (CPU) queues requests itself and stays up between films, so the
    # lanes voice side by side: one film's audit and ASR overlap another's
    # synthesis instead of waiting for the whole stage 1-2.
    if os.environ.get("DOCUMENTARY_VOICE_ENGINE", "").strip().lower() == "pocket":
        rc, tail = drive(folder, 1, 2)
        if rc != 0:
            return rc, tail
        rc2, tail2 = drive(folder, 3, 4)
        return rc2, tail + " | " + tail2
    while True:
        try:
            fd = os.open(str(VOICE_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode()); os.close(fd)
            break
        except FileExistsError:
            # a lock older than 40 minutes belongs to a dead lane
            if time.time() - VOICE_LOCK.stat().st_mtime > 2400:
                VOICE_LOCK.unlink(missing_ok=True)
            time.sleep(30)
    try:
        rc, tail = drive(folder, 1, 2)
    finally:
        VOICE_LOCK.unlink(missing_ok=True)
    # The cold start takes minutes on a full GPU (TOPIC_6 failed three times
    # on it), so the service stays up while any film still needs a voice.
    def needs_voice():
        return any(not (CODEX / d.name / "scene_timeline.json").exists()
                   and not any(OUT.glob("%02d_*.zip" % int(d.name.split("_")[1])))
                   for d in SRC.iterdir() if d.is_dir() and d.name.startswith("TOPIC_"))
    if not VOICE_LOCK.exists() and not needs_voice():
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-NetTCPConnection -LocalPort 7862 -State Listen -EA SilentlyContinue | "
                        "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -Confirm:$false }"],
                       capture_output=True)
    if rc != 0:
        return rc, tail
    rc2, tail2 = drive(folder, 3, 4)
    return rc2, tail + " | " + tail2


def free_gb():
    return shutil.disk_usage("C:\\").free / 1e9


def stay_awake():
    """Keep Windows from idle-sleeping while this batch runs (released when it exits).

    The machine slept at 03:13 and 06:13 under the 15-minute AC sleep setting
    and stalled a night of work; this asks for the system to stay up, the way a
    video player does, without changing any setting.
    """
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    except Exception:
        pass


def main():
    stay_awake()
    topics = sorted((d for d in SRC.iterdir() if d.is_dir() and d.name.startswith("TOPIC_")),
                    key=lambda d: int(d.name.split("_")[1]))
    for src in topics:
        n = int(src.name.split("_")[1])
        narration = next(src.glob("*NARRATION_ONLY.txt"))
        title = re.sub(r"^TOPIC_\d+_|_NARRATION_ONLY$", "", narration.stem).title().replace("_", "_")
        target = OUT / ("%02d_%s.zip" % (n, title))
        if target.exists():
            log("%s: already delivered (%s)" % (src.name, target.name))
            continue
        # Two lanes share the list: the lane that creates the claim file first
        # makes the film; a stale claim (no live lane) is removed by hand.
        claims = OUT / "claims"
        claims.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(claims / src.name), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode()); os.close(fd)
        except FileExistsError:
            continue
        if free_gb() < 25:
            log("%s: only %.0f GB free, stopping the batch" % (src.name, free_gb()))
            return
        folder = FILMS / src.name
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(narration, folder / narration.name)
        shutil.copy2(next(src.glob("*.wav")), folder / next(src.glob("*.wav")).name)
        (folder / "film_settings.json").write_text(json.dumps({"profile": "wildlife"}), encoding="utf-8")
        started = time.time()
        log("%s: start (%s, %.0f GB free)" % (src.name, title, free_gb()))
        # Stage 1-2 fail on passing service errors (voice port, a reset
        # connection, a Flash scene split): up to three clean starts. Once
        # stage 2 has passed, stage 3-4 is retried up to five times; the
        # old rule retried it once and left TOPIC_2/3 one shot short for
        # two hours (2026-10-25).
        rc, tail = voice_then_rest(folder)
        starts = 1
        while rc != 0 and "stage 2] http=200" not in tail and starts < 3:
            starts += 1
            for lock in ("run.lock", "pipeline.lock"):
                (CODEX / src.name / lock).unlink(missing_ok=True)
            rc, tail = voice_then_rest(folder)
        tries = 0
        while rc != 0 and (CODEX / src.name / "scene_timeline.json").exists() and tries < 5:
            tries += 1
            for lock in ("run.lock", "pipeline.lock"):
                (CODEX / src.name / lock).unlink(missing_ok=True)
            # Step 3 runs again and re-checks every shot (see finish_films.py).
            (CODEX / src.name / "03_materials" / "material_result.json").unlink(missing_ok=True)
            rc, tail = drive(folder, 3, 4)
        minutes = (time.time() - started) / 60
        zips = sorted((ENGINEERED / src.name).glob("*.zip")) if (ENGINEERED / src.name).exists() else []
        if rc == 0 and zips:
            shutil.copy2(zips[-1], target)
            log("%s: DELIVERED in %.0f min -> %s (%.1f GB)" % (src.name, minutes, target.name, target.stat().st_size / 1e9))
            report = CODEX / src.name / "03_materials" / "render_result.json"
            if report.exists():
                r = json.loads(report.read_text(encoding="utf-8"))
                log("  status %s, %s s, %s shots" % (r.get("status"), r.get("duration_sec"), r.get("shot_count")))
            shutil.rmtree(CODEX / src.name, ignore_errors=True)
            shutil.rmtree(ENGINEERED / src.name, ignore_errors=True)
        else:
            log("%s: NOT delivered after %.0f min (rc=%d); work folder kept for repair" % (src.name, minutes, rc))
    log("batch done")


if __name__ == "__main__":
    main()
