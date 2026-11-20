"""ucuz_ajan: Claude Code'u (araclariyla) freellmapi /v1/messages uzerinden bedava modelle kosturur.
Kullanim: python ucuz_ajan.py "gorev" [--model xkiro:mistralai/mistral-large-2512] [--tools Bash,Glob,Read,Grep] [--turns 25] [--cwd DIR]
Olcum 11-20: basit dosya gorevi OK, ama 8 gercek ajan gorevinde 5-6/16 (beyin/ders/bedava-model-ajan-yetersiz-1120). Sonnet/Haiku yerine KULLANMA; yalniz deneme.
Cikti modelin son mesaji; hata/bossa exit 1 -> Haiku/Sonnet ajanina don. Istemler saglayiciya gider: gizli bilgi verme."""
import argparse, os, shutil, sqlite3, subprocess, sys
DB = r"C:/Users/meteh/testbench/freellmapi/server/data/freeapi.db"
ap = argparse.ArgumentParser(); ap.add_argument("gorev")
ap.add_argument("--model", default="xkiro:mistralai/mistral-large-2512")
ap.add_argument("--tools", default="Bash,Glob,Read,Grep"); ap.add_argument("--turns", default="25")
ap.add_argument("--cwd", default=os.getcwd()); ap.add_argument("--hat", choices=["free", "9router"], default="free"); ap.add_argument("--timeout", type=int, default=900)
a = ap.parse_args()
if a.hat == "9router":  # VDS 9router, ChatGPT (cx/gpt-6.2-sol vb.) /v1/messages
    base, key = "http://100.104.78.117:20128", os.environ["NINEROUTER_API_KEY"]
else:
    base, key = "http://127.0.0.1:3001", None
key = key or sqlite3.connect(DB).execute("SELECT value FROM settings WHERE key='unified_api_key'").fetchone()[0]
keep = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC", "PATHEXT")
env = {k: os.environ[k] for k in keep if k in os.environ}  # masaustu oturum kimligi tasinmasin (yoksa 401)
env.update(ANTHROPIC_BASE_URL=base, ANTHROPIC_API_KEY=key, CLAUDE_CODE_SIMPLE="1", DISABLE_TELEMETRY="1")
cmd = [shutil.which("claude"), "-p", a.gorev, "--model", a.model, "--allowedTools", a.tools, "--max-turns", a.turns]
r = subprocess.run(cmd, env=env, cwd=a.cwd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=a.timeout)
out = "\n".join(l for l in r.stdout.splitlines() if "unrecognized_model" not in l).strip()
print(out or r.stderr[-500:]); sys.exit(0 if r.returncode == 0 and out and "API Error" not in out else 1)
