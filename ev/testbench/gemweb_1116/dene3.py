import asyncio, sys
from gemini_webapi import GeminiClient
from ffcookie import oku
async def main():
    ck = oku("ztjp9him.default-release"); d = {n: v for n, v, h in ck}
    print("cerez sayisi", len(ck))
    c = GeminiClient(d["__Secure-1PSID"], d.get("__Secure-1PSIDTS"))
    for n, v, h in ck:
        if n not in ("__Secure-1PSID", "__Secure-1PSIDTS"): c._cookies.set(n, v, domain=h)
    await c.init(timeout=120, auto_close=False, auto_refresh=False)
    print("DURUM", c.account_status.name)
    print("MODELLER", [str(m) for m in (c.list_models() or [])])
    print("USAGE", getattr(c, "usage_info", None)); print("QUOTA", c.quotas)
asyncio.run(main())
