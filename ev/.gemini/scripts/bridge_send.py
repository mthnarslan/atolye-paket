"""
Codex-to-Antigravity IPC Bridge.
Allows Codex (or external terminal) to queue messages/directives directly
for active Antigravity conversations.
"""
import sys
import json
import time
from pathlib import Path

BRIDGE_DIR = Path(r"C:\Users\meteh\.gemini\bridge")
BRIDGE_DIR.mkdir(parents=True, exist_ok=True)

INBOX = BRIDGE_DIR / "inbox.json"
OUTBOX = BRIDGE_DIR / "outbox.json"


def send_to_antigravity(conv_id: str, sender: str, directive: str, task_type: str = "COMMAND") -> None:
    """Queue a message for Antigravity from Codex."""
    messages = []
    if INBOX.exists():
        try:
            messages = json.loads(INBOX.read_text(encoding="utf-8"))
        except Exception:
            messages = []

    payload = {
        "id": f"msg_{int(time.time()*1000)}",
        "timestamp": time.time(),
        "target_conv_id": conv_id,
        "sender": sender,
        "task_type": task_type,
        "directive": directive,
        "status": "PENDING"
    }

    messages.append(payload)
    INBOX.write_text(json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[BRIDGE SUCCESS] Message queued for conversation {conv_id[:8]} -> Task: {task_type}")


def read_outbox(conv_id: str = None) -> list:
    """Read results written back by Antigravity."""
    if not OUTBOX.exists():
        return []
    try:
        data = json.loads(OUTBOX.read_text(encoding="utf-8"))
        if conv_id:
            return [m for m in data if m.get("conv_id") == conv_id]
        return data
    except Exception:
        return []


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python bridge_send.py <conv_id> '<directive>' [--sender <name>]")
        sys.exit(1)

    target_id = sys.argv[1]
    msg = sys.argv[2]
    sndr = "CODEX-SUPERVISOR"
    if "--sender" in sys.argv:
        idx = sys.argv.index("--sender")
        if idx + 1 < len(sys.argv):
            sndr = sys.argv[idx + 1]

    send_to_antigravity(target_id, sndr, msg)
