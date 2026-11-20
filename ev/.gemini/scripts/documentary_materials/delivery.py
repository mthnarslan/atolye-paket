"""Step 4 delivery package: the finished film and its parts in one ZIP.

The layout is the old five-folder delivery standard plus the shot clips:
a friend of the channel re-cuts films from the clips, so every clip is
numbered in timeline order and carries its own stretch of the voice;
played in name order they are the film.

The ZIP is written straight from the run's files, not from a copied
delivery folder, so a 2 GB package needs 2 GB of disk, not 4. It goes
to the channel folder, <DELIVERY_ROOT>/<film folder>/, so every finished
film lives in one place. The raw source downloads (the bulk of a run,
~11 GB) are then deleted from the local working folder; the rest of the
working folder stays local and small.
"""
import os
import json
import re
import time
import zipfile
from pathlib import Path

from .io import event, load, save, sha

FPS = 25
DELIVERY_ROOT = Path(os.environ.get("DOCUMENTARY_DELIVERY_ROOT",
                                    r"C:\Users\meteh\OneDrive\Desktop\Channells\ENGINEERED"))
RAW_MEDIA = (".mp4", ".webm", ".mkv", ".mov", ".m4v", ".ogv", ".part")


def _clock(seconds, sep=","):
    ms = max(0, round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def _sentences(project):
    """Sentence-level (start, end, text) from the voice word alignment."""
    words = load(project / "voice_word_alignment.json")["words"]
    rows, current = [], []
    for word in words:
        current.append(word)
        if re.search(r"[.!?][\"')\]]*$", word["word"]) or word is words[-1]:
            rows.append((current[0]["start"], current[-1]["end"], " ".join(w["word"] for w in current)))
            current = []
    if not rows:
        raise ValueError("Voice alignment has no words; refusing to package empty subtitles")
    return rows


def _edl(plan, out):
    """The cut list a re-edit needs: clip name, timeline span, medium, source."""
    rows = []
    for index, shot in enumerate(plan["shots"], 1):
        result = load(out / "shots" / f'{shot["shot_id"]:04d}' / "result.json")
        artifact = result["artifact"]
        start = shot["frame_start"] / FPS
        rows.append({
            "clip": f'{index:03d}_{int(start // 60):02d}m{int(start % 60):02d}s_{artifact["category"]}.mp4',
            "shot_id": shot["shot_id"], "start_sec": start, "end_sec": shot["frame_end"] / FPS,
            "category": artifact["category"], "narration": shot.get("narration"),
            "visual_fit": ((result.get("review") or {}).get("data") or {}).get("visual_fit"),
            "sources": [{"origin": s.get("origin_id"), "source_url": s.get("source_url"),
                         "start_sec": s.get("source_start_sec", s.get("start")),
                         "end_sec": s.get("source_end_sec", s.get("end"))}
                        for s in (artifact.get("source_segments") or [artifact]) if s.get("origin_id")],
            "path": artifact["path"]})
    return rows


def package(project, out):
    """Write <PROJECT>_DELIVERY_PACKAGE.zip to the local Desktop; return its path."""
    project, out = Path(project), Path(out)
    started = time.perf_counter()
    report = load(out / "render_result.json")
    video = Path(report["video"])
    if sha(video) != report["video_sha256"]:
        raise ValueError("Final video does not match its render report; package not created")
    name = project.name.upper()
    target = DELIVERY_ROOT / project.name / f"{name}_DELIVERY_PACKAGE.zip"
    receipt = out / "delivery_package.json"
    if target.is_file() and receipt.is_file() and load(receipt).get("video_sha256") == report["video_sha256"]:
        return str(target)

    plan = load(out / "material_plan.json")
    edl = _edl(plan, out)
    sentences = _sentences(project)
    srt = "\n".join(f"{i}\n{_clock(a)} --> {_clock(b)}\n{t}\n" for i, (a, b, t) in enumerate(sentences, 1))
    script = "\n".join(f"[{_clock(a, '.')} - {_clock(b, '.')}] {t}" for a, b, t in sentences) + "\n"
    readme = (f"# {name} teslim paketi\n\n"
              "1. `01_Bitmis_Tam_Video/` nihai video\n"
              "2. `02_Ses_Master/` master seslendirme\n"
              "3. `03_Altyazi_ve_Metin/` cümle zamanlı SRT ve metin\n"
              "4. `04_Gorsel_Materyaller/` anahtar kareler\n"
              "5. `05_EDL_ve_Raporlar/` kesim listesi (EDL.json) ve render raporu\n"
              f"6. `06_Klipler/` {len(edl)} sahne klibi, kendi ses parçasıyla; ad sırasıyla "
              "art arda konunca film birebir oluşur\n")

    pending = target.with_suffix(".zip.pending")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        zf.write(video, f"01_Bitmis_Tam_Video/{video.name}")
        zf.write(project / "master_voiceover.wav", "02_Ses_Master/master_voiceover.wav")
        zf.writestr("03_Altyazi_ve_Metin/subtitles.srt", srt)
        zf.writestr("03_Altyazi_ve_Metin/full_script.txt", script)
        for row in edl[::max(1, len(edl) // 12)][:12]:
            contact = Path(row["path"]).with_name("contact.jpg")
            if contact.is_file():
                zf.write(contact, f'04_Gorsel_Materyaller/keyframes/{row["clip"][:-4]}.jpg')
        zf.writestr("05_EDL_ve_Raporlar/EDL.json",
                    json.dumps([{k: v for k, v in r.items() if k != "path"} for r in edl], indent=2, ensure_ascii=False))
        zf.write(out / "render_result.json", "05_EDL_ve_Raporlar/render_result.json")
        zf.writestr("05_EDL_ve_Raporlar/DELIVERY_REPORT.md", readme)
        for row in edl:
            zf.write(row["path"], f'06_Klipler/{row["clip"]}')
    with zipfile.ZipFile(pending) as zf:
        bad = zf.testzip()
    if bad:
        pending.unlink(missing_ok=True)
        raise ValueError(f"Delivery ZIP failed its CRC check at {bad}")
    pending.replace(target)
    save(receipt, {"zip": str(target), "video_sha256": report["video_sha256"], "clips": len(edl),
                   "bytes": target.stat().st_size})
    event(out, "delivery_packaged", zip=str(target), clips=len(edl),
          freed_raw_bytes=_drop_raw_sources(out), elapsed_seconds=round(time.perf_counter() - started, 3))
    return str(target)


def _drop_raw_sources(out):
    """Delete the downloaded source footage once the film is packaged.

    The finished shots, voice and reports stay, so step 4 can be reused;
    producing shots again (step 3) would need the sources fetched again.
    """
    freed = 0
    for folder in (out / "sources", out / "source_recovery"):
        for path in folder.rglob("*") if folder.is_dir() else ():
            if path.is_file() and path.suffix.lower() in RAW_MEDIA:
                size = path.stat().st_size
                # A file another film's thread still has open (Windows
                # refuses the delete) stays; the package is already written
                # and the batch removes the whole folder later (PAR_1, TEST_A).
                try:
                    path.unlink()
                    freed += size
                except PermissionError:
                    pass
    return freed
