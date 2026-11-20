"""Build a full V3 delivery ZIP per film: final video, voiceover, narration, edit plan, contact sheet, used clips/images, fact check."""
import sys, zipfile
from pathlib import Path

WORK = Path(r"C:\Users\meteh\Kanallar\Engineered\scenefile\work")
CODEX = Path(r"C:\Users\meteh\CodexOutputs")
OUT = Path(r"C:\Users\meteh\OneDrive\Desktop\Channells\ENGINEERED")


def build(film):
    w, c, o = WORK / film, CODEX / film, OUT / film
    video = o / f"{film}_WRATH_OF_EARTH_V3.mp4"
    assert video.is_file(), video
    items = [(video, video.name),
             (w / "voice_n16.wav", "audio/voiceover_master.wav"),
             (w / f"{film}_WRATH_OF_EARTH_V3_sheet.jpg", "qa/contact_sheet.jpg"),
             (w / "plan.json", "edit/edit_plan.json"),
             (w / "sections.json", "edit/sections.json"),
             (c / "narration.txt", "script/narration.txt"),
             (c / "factcheck.md", "script/factcheck.md")]
    for sub in ("clips", "img"):
        for f in sorted((w / "assets" / sub).rglob("*")):
            if f.is_file():
                items.append((f, f"assets/{sub}/{f.relative_to(w / 'assets' / sub).as_posix()}"))
    dst = o / f"{film.upper()}_V3_PACKAGE.zip"
    tmp = dst.with_suffix(".part")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for src, arc in items:
            if src.is_file():
                z.write(src, arc)
            else:
                print("  missing", src)
    tmp.replace(dst)
    with zipfile.ZipFile(dst) as z:
        bad = z.testzip()
    print(f"{film}: {dst.stat().st_size/2**20:.0f} MB, {len(items)} files, test={'OK' if bad is None else bad}", flush=True)


for film in sys.argv[1:]:
    build(film)
