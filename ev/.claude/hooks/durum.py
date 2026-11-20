# SessionStart: oturum basinda / sikistirmadan sonra calisilan klasorun DURUM.md'sini baglama geri koyar.
import json, sys
from pathlib import Path
try:
    cwd = Path(json.load(sys.stdin).get("cwd") or ".")
except Exception:
    cwd = Path(".")
for f in (cwd / ".claude" / "DURUM.md", cwd / "DURUM.md"):
    if f.is_file():
        t = f.read_text(encoding="utf-8", errors="replace")
        sys.stdout.reconfigure(encoding="utf-8")
        print(f"# Suren is durumu ({f})\n" + t[:8000])
        break
