import asyncio, sys, time
sys.path.insert(0, ".")
import authuser; authuser.kur()
from gemini_webapi import GeminiClient
from ffcookie import oku
async def bir(n, ck):
    authuser.AU.set(n)
    m = {a: v for a, v, h in ck}
    c = GeminiClient(m["__Secure-1PSID"], m.get("__Secure-1PSIDTS"))
    for a, v, h in ck:
        if a not in ("__Secure-1PSID", "__Secure-1PSIDTS"): c._cookies.set(a, v, domain=h)
    await c.init(timeout=120, auto_close=False, auto_refresh=False)
    u = c.usage_info or {}
    w0 = (u.get("weekly") or {}).get("remaining_credits"); h0 = (u.get("current_5h") or {}).get("remaining_credits")
    r = await c.generate_content(f"What is {n}+40? Number only.", model="gemini-flash-lite", temporary=True)
    await c._fetch_quota(); u = c.usage_info or {}
    print(n, c.account_status.name, (u.get("tier") or {}).get("label"), "5s", h0, "->", (u.get("current_5h") or {}).get("remaining_credits"),
          "hafta", w0, "->", (u.get("weekly") or {}).get("remaining_credits"), "| cevap", r.text.strip()[:30], "| modeller", [getattr(x, "model_name", x) for x in c.list_models() or []], flush=True)
async def main():
    ck = oku("ztjp9him.default-release")
    for n in range(5):
        try: await asyncio.create_task(bir(n, ck))
        except Exception as e: print(n, "HATA", type(e).__name__, str(e)[:200], flush=True)
asyncio.run(main())
