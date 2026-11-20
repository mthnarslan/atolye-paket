"""ucuz_llm: mekanik isleri (sayma, ayiklama, siralama, kisa ceviri, log ozeti, JSON) Claude limiti harcamadan
freellmapi (testbench/freellmapi, :3001) uzerinden ucretsiz modellere yaptirir.

Kalite gereken is (tasarim, QA/hakem, Ingilizce metin, karar) burada YAPILMAZ.
Cevabi her zaman kendin kontrol et (json/sayi/kod); hata ya da bos cevapta exit 1 -> Haiku'ya don.
Kilo istemleri egitim icin loglar: gizli bilgi (anahtar, e-posta, hesap) gonderme.

Kullanim:
  python ucuz_llm.py "17*23 kac? yalnizca sayi"
  echo "metin" | python ucuz_llm.py -s "Bu metindeki tarihleri listele"
  python ucuz_llm.py --json "..."                 # cevaptan ilk JSON'u ayiklar, gecersizse exit 1
  python ucuz_llm.py --batch girdi.jsonl > cikti.jsonl   # her satir {"id":..,"prompt":..}; paralel 6
Python'dan:  from ucuz_llm import sor;  sor("...")  -> str (hata: RuntimeError)
"""
import argparse, json, os, re, sqlite3, sys, threading, time, urllib.request, concurrent.futures as cf

URL = os.environ.get("UCUZ_LLM_URL", "http://127.0.0.1:3001/v1/chat/completions")
DB = r"C:/Users/meteh/testbench/freellmapi/server/data/freeapi.db"
# 11-20 olcumu (beyin/kaynak/freellmapi-ilk-olcum-1120): cevap verenlerde dogruluk sirasi.
# Anahtar eklenince buraya guclu modelleri one ekle; "auto" son care.
# 11-20 anahtarli olcum: mistral-large/medium (xkiro), command-a-plus (cohere), nemotron-3.5-super-vl (openrouter) 10/10.
MODELS = os.environ.get("UCUZ_LLM_MODELS", "xkiro:mistralai/mistral-large-2512,cohere:command-a-plus-05-2026,"
                        "xkiro:mistralai/mistral-medium-3.5,openrouter:nvidia/nemotron-3.5-super-vl:free,"
                        "agnes:agnes-3.0-flash,cohere:command-a-03-2025,"
                        "kilo-auto,nemotron-3-ultra-550b,gpt-oss-120b,qwen2.5-vl-72b,"
                        "gpt-oss-20b,qwen3.8-27b,nemotron-3-nano-omni-reasoning,auto").split(",")
_cool, _lock, _rr = {}, threading.Lock(), [0]
_key = None


def _k():
    global _key
    if _key is None:
        _key = sqlite3.connect(DB).execute("SELECT value FROM settings WHERE key='unified_api_key'").fetchone()[0]
    return _key


def _call(model, msgs, max_tokens, timeout):
    body = json.dumps({"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": 0}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Authorization": "Bearer " + _k(), "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=timeout))
    txt = (d["choices"][0]["message"].get("content") or "").strip()
    return re.sub(r"<think>.*?</think>", "", txt, flags=re.S).strip()


def sor(prompt, system=None, max_tokens=800, timeout=45, want_json=False):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    with _lock:  # toplu modda yuku modellere dagit
        start = _rr[0] % len(MODELS); _rr[0] += 1
    order = MODELS[start:] + MODELS[:start] if start else MODELS
    errs = []
    for m in order:
        if _cool.get(m, 0) > time.time():
            continue
        try:
            a = _call(m, msgs, max_tokens, timeout)
            if not a:
                raise ValueError("bos cevap")
            if want_json:
                j = re.search(r"[\[{].*[\]}]", a, re.S)
                a = json.dumps(json.loads(j.group(0)), ensure_ascii=False)
            return a
        except Exception as e:
            msg = getattr(e, "read", lambda: b"")().decode(errors="ignore")[:100] or str(e)[:100]
            errs.append(f"{m}: {msg}")
            if "rate" in msg.lower() or "exhausted" in msg.lower() or "429" in msg:
                _cool[m] = time.time() + 60
    raise RuntimeError("ucuz_llm: tum modeller basarisiz -> Haiku'ya don | " + " ; ".join(errs[-3:]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("-s", "--system")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-tokens", type=int, default=800)
    ap.add_argument("--batch")
    ap.add_argument("--paralel", type=int, default=6)
    a = ap.parse_args()
    if a.batch:
        rows = [json.loads(l) for l in open(a.batch, encoding="utf-8") if l.strip()]
        def one(r):
            try:
                return {"id": r.get("id"), "ok": True, "cevap": sor(r["prompt"], r.get("system", a.system), a.max_tokens, want_json=a.json)}
            except Exception as e:
                return {"id": r.get("id"), "ok": False, "hata": str(e)[:300]}
        bad = 0
        with cf.ThreadPoolExecutor(a.paralel) as ex:
            for out in ex.map(one, rows):
                bad += not out["ok"]
                print(json.dumps(out, ensure_ascii=False), flush=True)
        sys.exit(1 if bad else 0)
    # stdin yalniz prompt verilmediyse ya da "-" ise okunur (aksi halde acik pipe'ta sonsuza dek bekler)
    p = a.prompt or ""
    if not p or p == "-":
        p = sys.stdin.read()
    if not p.strip():
        sys.exit("prompt yok")
    try:
        print(sor(p, a.system, a.max_tokens, want_json=a.json))
    except Exception as e:
        print(e, file=sys.stderr); sys.exit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
