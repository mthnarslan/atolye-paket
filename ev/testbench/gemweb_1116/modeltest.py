import asyncio, time, json
from gemini_webapi import GeminiClient
from ffcookie import oku
SES = r"C:/Users/meteh/testbench/tur_dil_1115/cut/-1_VePsFdFM_orj.mp3"
async def main():
    ck = oku("ztjp9him.default-release"); d = {n: v for n, v, h in ck}
    c = GeminiClient(d["__Secure-1PSID"], d.get("__Secure-1PSIDTS"))
    for n, v, h in ck:
        if n not in ("__Secure-1PSID", "__Secure-1PSIDTS"): c._cookies.set(n, v, domain=h)
    await c.init(timeout=120, auto_close=False, auto_refresh=False)
    ms = c.list_models() or []
    for m in ms: print("M", {k: getattr(m, k) for k in dir(m) if not k.startswith("_") and not callable(getattr(m, k))})
    def kredi(): u = c.usage_info or {}; return (u.get("current_5h", {}).get("remaining_credits"), u.get("weekly", {}).get("remaining_credits"))
    for m in ms:
        for tur in ("metin", "ses"):
            k0 = kredi(); t = time.time()
            try:
                if tur == "metin": r = await c.generate_content("What is 17*23? Answer with the number only.", model=m, temporary=True)
                else: r = await c.generate_content("Listen. One line: spoken language, speaker gender, 8-word summary.", files=[SES], model=m, temporary=True)
                out = r.text.strip().replace("\n", " ")[:140]
            except Exception as e: out = f"HATA {type(e).__name__}: {str(e)[:140]}"
            sn = round(time.time() - t, 1)
            try: await c._fetch_quota()
            except Exception as e: pass
            print(f"T {m.model_name if hasattr(m,'model_name') else m} | {tur} | {sn} sn | kredi {k0} -> {kredi()} | {out}", flush=True)
            await asyncio.sleep(20)
asyncio.run(main())
