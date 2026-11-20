"""Run drive.py against the stub server, one case each, and check exit code + REASON line."""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).parent
DRIVE = str(HERE.parent / "drive.py")
PORT = 8299
srv = subprocess.Popen([sys.executable, str(HERE / "stub_server.py"), str(PORT)])
time.sleep(1.5)
codex = Path(tempfile.mkdtemp())
(codex / "reaudit_case").mkdir()
(codex / "reaudit_case" / "voice_manifest.json").write_text("{}")
env = {**os.environ, "DRIVE_BRIDGE_URL": f"http://127.0.0.1:{PORT}/run", "DRIVE_HTTP_TIMEOUT": "2", "DRIVE_CODEX_OUT": str(codex),
       "DRIVE_AUDIT": str(HERE / "fake_audit.py"), "DRIVE_REAUDIT_PAUSE": "0", "DRIVE_REAUDIT_TIMEOUT": "3", "DRIVE_HEARTBEAT": "1", "DRIVE_STALL": "100",
       "PYTHONIOENCODING": "utf-8"}
CASES = [("timeout_case", 10, "transport"), ("reset_case", 10, "transport"), ("hang_case", 10, "stalled"), ("nonjson_case", 10, "non_json"),
         ("alloc_case", 3, "stage3_fail"), ("dup_case", 11, "duplicate_job"), ("stage1fail_case", 1, "stage1_fail"),
         ("reaudit_case", 12, "reaudit_timeout"), ("success_case", 0, None)]
bad = 0
try:
    for name, want, cls in CASES:
        r = subprocess.run([sys.executable, DRIVE, "C:/x/" + name], env={**env, **({"DRIVE_STALL": "3", "DRIVE_HTTP_TIMEOUT": "60"} if name.startswith("hang") else {})}, capture_output=True, text=True, timeout=60)
        reasons = [l for l in r.stdout.splitlines() if l.startswith("REASON")]
        ok = r.returncode == want and (len(reasons) == 1 and reasons[0].split()[1] == cls if cls else not reasons and "ALL STAGES DONE" in r.stdout)
        bad += not ok
        print("%-5s %-16s exit %2d (want %2d) %s" % ("OK" if ok else "FAIL", name, r.returncode, want, reasons[0][:150] if reasons else r.stdout.strip().splitlines()[-1]))
finally:
    srv.kill()
sys.exit(bad)
