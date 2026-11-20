"""Stub bridge for drive.py tests: the case is the folder name's prefix (case_<name>)."""
import json, socket, struct, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, raw=False):
        data = body if raw else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        case, stage = req["folder_path"].replace("\\", "/").split("/")[-1], req["stage"]
        ok = {1: "PASS", 2: "PASS", 3: "MATERIALS_READY", 4: "PASS"}[stage]
        if case.startswith("timeout") and stage == 1:
            time.sleep(6)
        elif case.startswith("hang") and stage == 1:
            time.sleep(40)
        elif case.startswith("reset") and stage == 1:
            self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            self.rfile.close()
            self.wfile.close()
            self.connection.close()
            return
        elif case.startswith("nonjson") and stage == 1:
            self.send(200, b"<html>oops</html>", raw=True)
        elif case.startswith("alloc") and stage == 3:
            self.send(500, {"status": "FAIL", "error_type": "ValueError", "error": "No feasible narrative/category allocation after bounded Codex replan"})
        elif case.startswith("dup") and stage == 1:
            self.send(500, {"error_type": "RuntimeError", "error": "This output already has an active production job; wait for cancellation to finish"})
        elif case.startswith("stage1fail") and stage == 1:
            self.send(200, {"status": "FAIL", "next_step_allowed": False, "summary": "reference voice mismatch"})
        elif case.startswith("reaudit") and stage == 1:
            self.send(200, {"status": "PASS_DEGRADED", "next_step_allowed": True})
        else:
            self.send(200, {"status": ok, "next_step_allowed": True})


ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
