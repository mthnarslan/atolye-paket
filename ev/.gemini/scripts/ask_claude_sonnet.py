import sys
import os
import json
import urllib.request
import urllib.error
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vds_secret_store import read_secret

ROUTER_URL = "http://100.104.78.117:20128/v1/chat/completions"
ROUTER_API_KEY = read_secret("codex_router")

from ask_frontier_models import PROMPT, stream_query

if __name__ == "__main__":
    out_dir = Path(r"C:\Users\meteh\.gemini\antigravity\brain\519fe672-73a8-4624-999d-0643c27eb7f4\consultation")
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        print("[Claude-Sonnet] Querying ag/claude-sonnet-4-6 via 9Router (port 20128) with streaming...", flush=True)
        res, dur = stream_query(ROUTER_URL, ROUTER_API_KEY, "ag/claude-sonnet-4-6", PROMPT, timeout=120)
        with open(out_dir / "response_claude_sonnet_4_6.md", "w", encoding="utf-8") as f:
            f.write(res)
        print(f"[Claude-Sonnet] Completed in {dur}s ({len(res)} chars). Saved to response_claude_sonnet_4_6.md", flush=True)
    except Exception as e:
        print(f"[Claude-Sonnet] FAILED: {e}", flush=True)
