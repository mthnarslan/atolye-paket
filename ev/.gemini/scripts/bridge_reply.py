"""
Antigravity-to-Codex IPC Bridge reply utility.
Writes execution reports, test proofs, and metrics back to outbox.
"""
import sys
import json
import time
from pathlib import Path

BRIDGE_DIR = Path(r"C:\Users\meteh\.gemini\bridge")
OUTBOX = BRIDGE_DIR / "outbox.json"


def reply_to_codex(conv_id: str, status: str, report: str, metrics: dict = None) -> None:
    """Write an execution report back to Codex."""
    entries = []
    if OUTBOX.exists():
        try:
            entries = json.loads(OUTBOX.read_text(encoding="utf-8"))
        except Exception:
            entries = []

    payload = {
        "id": f"rep_{int(time.time()*1000)}",
        "timestamp": time.time(),
        "conv_id": conv_id,
        "status": status,
        "report": report,
        "metrics": metrics or {}
    }

    entries.append(payload)
    OUTBOX.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[BRIDGE REPLY] Report sent to Codex for conversation {conv_id[:8]} -> Status: {status}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python bridge_reply.py <conv_id> <status> '<report>'")
        sys.exit(1)

    cid = sys.argv[1]
    st = sys.argv[2]
    rep = sys.argv[3]
    reply_to_codex(cid, st, rep)
