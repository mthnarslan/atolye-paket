"""10 paralel kisa metin istegi: hangi hesap, sure, durum."""
import json, time, concurrent.futures as cf, requests

U = "http://127.0.0.1:8790/v1/chat/completions"

def one(i):
    t = time.time()
    try:
        r = requests.post(U, json={"model": "gemini-4-hydrogen", "reasoning_effort": "low",
            "messages": [{"role": "user", "content": f"Reply with only the number {i*7}."}]}, timeout=180)
        j = r.json() if r.ok else {}
        txt = (j.get("choices") or [{}])[0].get("message", {}).get("content", "") if j else r.text[:120]
        return {"i": i, "http": r.status_code, "sec": round(time.time() - t, 1), "hesap": j.get("hesap"),
                "ok": str(i * 7) in txt, "txt": txt.strip()[:40]}
    except Exception as e:
        return {"i": i, "http": None, "sec": round(time.time() - t, 1), "err": str(e)[:120]}

t0 = time.time()
with cf.ThreadPoolExecutor(10) as ex:
    res = list(ex.map(one, range(1, 11)))
for r in res:
    print(json.dumps(r, ensure_ascii=False))
print("toplam", round(time.time() - t0, 1), "sn; dogru", sum(1 for r in res if r.get("ok")), "/10; ayri hesap", len({r.get("hesap") for r in res}))
