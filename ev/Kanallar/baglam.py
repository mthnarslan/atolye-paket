"""baglam: bu klasorun en son aktif ana oturumunun su anki baglam boyutu (son model cagrisi).
  python C:/Users/meteh/Kanallar/baglam.py            # cwd'nin oturumu
  python C:/Users/meteh/Kanallar/baglam.py <klasor>
Cikti tek satir: 'baglam 134k / esik 120k -> ELLE SIKISTIR' ya da '... -> devam'."""
import glob, json, os, re, sys
ESIK = 120_000
cwd = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
proj = os.path.expanduser('~/.claude/projects/' + re.sub(r'[^A-Za-z0-9]', '-', cwd))
files = [f for f in glob.glob(proj + '/*.jsonl')]
if not files: print(f'baglam: oturum bulunamadi ({proj})'); sys.exit(1)
f = max(files, key=os.path.getmtime)
ctx = 0
with open(f, 'rb') as h:
    h.seek(0, 2); h.seek(max(0, h.tell() - 3_000_000))
    for line in h.read().decode('utf-8', 'replace').splitlines():
        if '"usage"' not in line: continue
        try: u = (json.loads(line).get('message') or {}).get('usage') or {}
        except Exception: continue
        c = u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0) + u.get('input_tokens', 0)
        if c: ctx = c
print(f"baglam {ctx//1000}k / esik {ESIK//1000}k -> {'ELLE SIKISTIR (is bitince)' if ctx > ESIK else 'devam'}")
