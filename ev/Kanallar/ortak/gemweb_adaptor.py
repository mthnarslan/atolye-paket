"""OpenAI-uyumlu adaptor :8791 (ortak/gemweb_adaptor.py) -> sohbet: Kanallar/gemweb.py (hydrogen low, sayac), embeddings: hash tabanli torbasiz vektor (LLM'siz)."""
import sys, json, re, hashlib, math, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, r"C:/Users/meteh/Kanallar"); import gemweb
SAY = {"chat": 0, "emb": 0}
import os
LOG = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "gemweb_adaptor.log"), "a", encoding="utf-8")
D = 512

def vec(t):
    v = [0.0] * D
    for w in re.findall(r"\w+", t.lower()):
        h = int(hashlib.md5(w.encode()).hexdigest()[:8], 16)
        v[h % D] += 1 if (h >> 9) & 1 else -1 if False else 1
    n = math.sqrt(sum(x * x for x in v)) or 1
    return [x / n for x in v]

def metin(m):
    c = m["content"]
    if isinstance(c, list): c = "\n".join(p.get("text", "") for p in c)
    return f"[{m['role']}]\n{c}"

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path.endswith("/embeddings"):
            inp = d["input"]; inp = [inp] if isinstance(inp, str) else inp
            inp = [x if isinstance(x, str) else " ".join(map(str, x)) for x in inp]
            SAY["emb"] += len(inp)
            return self._send({"object": "list", "model": d.get("model"), "data": [{"object": "embedding", "index": i, "embedding": vec(t)} for i, t in enumerate(inp)], "usage": {"prompt_tokens": 0, "total_tokens": 0}})
        SAY["chat"] += 1
        prompt = "\n\n".join(metin(m) for m in d["messages"])
        t = time.time()
        try:
            out = gemweb.sor(prompt)
        except Exception as e:
            LOG.write(f"{time.strftime('%X')} chat#{SAY['chat']} HATA {str(e)[:150]}\n"); LOG.flush()
            return self._send({"error": {"message": str(e)[:200]}}, 502)
        LOG.write(f"{time.strftime('%X')} chat#{SAY['chat']} {len(prompt)}c -> {len(out)}c {time.time()-t:.0f}s\n"); LOG.flush()
        if d.get("stream"):
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
            ch = lambda delta, fin: "data: " + json.dumps({"id": "x", "object": "chat.completion.chunk", "model": "g", "choices": [{"index": 0, "delta": delta, "finish_reason": fin}]}) + "\n\n"
            self.wfile.write((ch({"role": "assistant", "content": out}, None) + ch({}, "stop") + "data: [DONE]\n\n").encode()); return
        self._send({"id": "x", "object": "chat.completion", "model": d.get("model", "g"), "choices": [{"index": 0, "message": {"role": "assistant", "content": out}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})

def baslat(port=8791):
    """Arka plan thread'inde baslatir; sayac SAY. GPT-Researcher/LangChain gibi OpenAI-uyumlu araclar OPENAI_BASE_URL=http://127.0.0.1:PORT/v1 ile gemweb'i kullanir."""
    srv = ThreadingHTTPServer(("127.0.0.1", port), H); threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv


if __name__ == "__main__":
    baslat(); threading.Event().wait()
