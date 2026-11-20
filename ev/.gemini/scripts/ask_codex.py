import sys
import os
import json
import urllib.request
import urllib.error
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vds_secret_store import read_secret

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VDS_URL = "http://100.104.78.117:8765/v1/chat/completions"
VDS_API_KEY = read_secret("codex_vds")

ROUTER_URL = "http://127.0.0.1:20128/v1/chat/completions"
ROUTER_API_KEY = read_secret("codex_router")

def ask_codex(prompt, model="gpt-6-sol", timeout=180):
    t0 = time.time()
    for url in [VDS_URL]:
        try:
            headers = {
                "Authorization": f"Bearer {VDS_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "stream": True
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            content_parts = []
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                for line in resp:
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if line_str.startswith("data: ") and not line_str.startswith("data: [DONE]"):
                        try:
                            chunk = json.loads(line_str[6:])
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                content_parts.append(delta["content"])
                        except Exception:
                            pass
            if content_parts:
                return "".join(content_parts).strip()
        except Exception as e:
            sys.stderr.write(f"[HYBRID_VDS] Endpoint {url} failed ({e}) in {round(time.time() - t0, 1)}s.\n")

    for r_url in [ROUTER_URL]:
        try:
            fb_headers = {
                "Authorization": f"Bearer {ROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            fb_payload = {
                "model": "ag/gemini-3.8-flash-high",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            fb_req = urllib.request.Request(r_url, data=json.dumps(fb_payload).encode("utf-8"), headers=fb_headers)
            with urllib.request.urlopen(fb_req, timeout=30) as fb_resp:
                body = fb_resp.read().decode("utf-8", errors="replace")
                
            content_parts = []
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("data: ") and not line.startswith("data: [DONE]"):
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            content_parts.append(delta["content"])
                    except Exception:
                        pass
            if content_parts:
                return "".join(content_parts).strip()
            if body.strip():
                return body.strip()
        except Exception as fe:
            sys.stderr.write(f"[HYBRID_ROUTER] Endpoint {r_url} failed: {fe}\n")

    return "Kritik Hata: Hem VDS Codex hem de 9Router Fallback basarisiz."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python ask_codex.py <soru> [--model <model_adi>]")
        sys.exit(1)
        
    prompt = sys.argv[1]
    model = "gpt-6-sol"
    if "--model" in sys.argv:
        m_idx = sys.argv.index("--model")
        if m_idx + 1 < len(sys.argv):
            model = sys.argv[m_idx + 1]
            
    response = ask_codex(prompt, model=model)
    print(response)
