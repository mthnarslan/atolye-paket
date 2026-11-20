import os
import sys
import glob
import json
import time
import datetime
import subprocess
from pathlib import Path

CODEX_DIR = Path(r"C:\Users\meteh\.codex")
SESSIONS_DIR = CODEX_DIR / "sessions"
LOCKS_DIR = CODEX_DIR / "thread-writer-locks"
CODEX_EXE = r"C:\Users\meteh\AppData\Local\Programs\Python\Python312\Scripts\codex-real.exe"

def get_active_threads():
    """Find currently locked threads (threads open in a Codex terminal)."""
    if not LOCKS_DIR.exists():
        return []
    locks = list(LOCKS_DIR.glob("*.lock"))
    thread_ids = []
    for l in locks:
        tid = l.stem
        if tid != ".coordination":
            thread_ids.append(tid)
    return thread_ids

def find_session_file(thread_id):
    """Find the rollout jsonl file for a given thread_id."""
    matches = list(SESSIONS_DIR.glob(f"**/*{thread_id}*.jsonl"))
    if matches:
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return matches[0]
    return None

def parse_iso_time(ts_str):
    try:
        # e.g. 2026-10-12T13:23:26.378Z
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        dt = datetime.datetime.fromisoformat(ts_str)
        return dt.timestamp()
    except Exception:
        return None

def analyze_thread(thread_id):
    sf = find_session_file(thread_id)
    if not sf:
        return {"thread_id": thread_id, "status": "FILE_NOT_FOUND"}
    
    with open(sf, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    last_event_type = None
    last_agent_msg = None
    last_user_msg = None
    is_completed = False
    last_ts = None
    
    for l in reversed(lines[-35:]):
        try:
            d = json.loads(l)
            if not last_ts and "timestamp" in d:
                last_ts = parse_iso_time(d["timestamp"])
            ptype = d.get("type")
            payload = d.get("payload", {})
            if isinstance(payload, dict):
                stype = payload.get("type")
                if stype == "task_complete" and not is_completed:
                    is_completed = True
                if stype == "message":
                    role = payload.get("role") or payload.get("sender")
                    content = payload.get("content")
                    if role == "assistant" and not last_agent_msg:
                        last_agent_msg = str(content)
                    elif role == "user" and not last_user_msg:
                        last_user_msg = str(content)
            if ptype == "event_msg" and not last_event_type:
                last_event_type = payload.get("type")
        except Exception:
            pass
            
    now = time.time()
    age_sec = int(now - last_ts) if last_ts else int(now - sf.stat().st_mtime)
    
    # Determine status
    if age_sec < 20:
        status = f"RUNNING ({age_sec}s ago)"
    elif is_completed:
        status = f"STOPPED / IDLE AT PROMPT ({age_sec}s ago)"
    else:
        status = f"WAITING ({age_sec}s ago)"
        
    return {
        "thread_id": thread_id,
        "file": str(sf),
        "status": status,
        "age_sec": age_sec,
        "is_completed": is_completed,
        "last_agent_msg": (last_agent_msg or "")[:120],
        "last_user_msg": (last_user_msg or "")[:120],
    }

def queue_message(thread_id, message="Devam et, durma; gorevi sonuna kadar tamamla ve gercek kanit sun."):
    cmd = [CODEX_EXE, "queue", "--thread", thread_id, "--message", message]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0, res.stdout.strip() or res.stderr.strip()

def main():
    threads = get_active_threads()
    if not threads:
        print("Aktif acik Codex oturumu bulunamadi.")
        return

    print("=" * 70)
    print("CODEX OTURUM DURUM RAPORU & CANLILIK DENETIMI")
    print("=" * 70)
    
    for i, tid in enumerate(threads, 1):
        info = analyze_thread(tid)
        print(f"[{i}] Thread: {info['thread_id']}")
        print(f"    Durum      : {info['status']}")
        if info.get("last_agent_msg"):
            print(f"    Son Mesaj  : {info['last_agent_msg']}")
        print("-" * 70)

    if "--wake-all" in sys.argv or "--resume" in sys.argv:
        print("\n[!] Durmus olan oturumlar uyandiriliyor...")
        for tid in threads:
            info = analyze_thread(tid)
            if info.get("is_completed") or info.get("age_sec", 0) > 40:
                ok, out = queue_message(tid)
                print(f"    -> Thread {tid}: {'UYANDIRILDI' if ok else 'HATA'} ({out})")

if __name__ == "__main__":
    main()
