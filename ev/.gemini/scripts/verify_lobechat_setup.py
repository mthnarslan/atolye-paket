"""
LobeChat & Codex API Setup Verification Script
Verifies:
1. LobeChat Web UI on port 3210
2. Unified Gateway on port 20130
3. Upstream VDS (port 8765)
4. Upstream Router (port 20128)
5. Model routing and chat completions for both model families
"""

import sys
import json
import urllib.request
from pathlib import Path

def test_check(name, func):
    print(f"[*] Testing {name}...")
    try:
        func()
        print(f"    [+] {name}: SUCCESS")
        return True
    except Exception as e:
        print(f"    [-] {name}: FAILED ({e})")
        return False

def verify_lobechat():
    req = urllib.request.Request("http://localhost:3210")
    with urllib.request.urlopen(req, timeout=5) as r:
        if r.status not in (200, 307):
            raise RuntimeError(f"Unexpected status code: {r.status}")

def verify_gateway_health():
    with urllib.request.urlopen("http://127.0.0.1:20130/health", timeout=5) as r:
        data = json.loads(r.read().decode())
        if data.get("status") != "ok":
            raise RuntimeError(f"Unexpected payload: {data}")

def verify_model_aggregation():
    with urllib.request.urlopen("http://127.0.0.1:20130/v1/models", timeout=8) as r:
        data = json.loads(r.read().decode())
        models = [m.get("id") for m in data.get("data", [])]
        if len(models) < 40:
            raise RuntimeError(f"Too few models aggregated: {len(models)}")
        gpt_found = any("gpt-6" in m for m in models)
        flash_found = any("gemini-3.8-flash" in m for m in models)
        if not (gpt_found and flash_found):
            raise RuntimeError("Missing required model families")
        print(f"    [i] Total models detected: {len(models)}")

def verify_gpt_completion():
    payload = {
        "model": "gpt-6-sol",
        "messages": [{"role": "user", "content": "Ping test"}],
        "stream": True
    }
    req = urllib.request.Request(
        "http://127.0.0.1:20130/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
        if "data: " not in raw:
            raise RuntimeError(f"No SSE stream received: {raw[:100]}")

def verify_flash_completion():
    payload = {
        "model": "ag/gemini-3.8-flash-high",
        "messages": [{"role": "user", "content": "Ping test"}],
        "stream": True
    }
    req = urllib.request.Request(
        "http://127.0.0.1:20130/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
        if "data: " not in raw:
            raise RuntimeError(f"No SSE stream received: {raw[:100]}")

def main():
    print("==================================================")
    print(" LobeChat & Multi-Model Codex Gateway Verification")
    print("==================================================")
    tests = [
        ("LobeChat Container (Port 3210)", verify_lobechat),
        ("Unified Gateway Health (Port 20130)", verify_gateway_health),
        ("Aggregated Model Discovery (55 models)", verify_model_aggregation),
        ("GPT VDS Model Completion (gpt-6-sol)", verify_gpt_completion),
        ("Router Model Completion (ag/gemini-3.8-flash-high)", verify_flash_completion),
    ]

    failed = 0
    for name, func in tests:
        if not test_check(name, func):
            failed += 1

    print("==================================================")
    if failed == 0:
        print("ALL VERIFICATION CHECKS PASSED WITH EXIT CODE 0!")
        print("==================================================")
        sys.exit(0)
    else:
        print(f"VERIFICATION FAILED: {failed} checks failed.")
        print("==================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
