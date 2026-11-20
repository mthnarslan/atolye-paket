import asyncio, json
from gemini_webapi import GeminiClient
d = json.load(open("hesaplar/hesap1.json", encoding="utf-8-sig"))
async def main():
    c = GeminiClient(d.get("psid") or d["__Secure-1PSID"], d.get("psidts") or d.get("__Secure-1PSIDTS"), verbose=True)
    await c.init(timeout=120, auto_close=False, auto_refresh=False)
    print("DURUM", c.account_status.name, "| kaynak", getattr(c, "_cookie_source", "?"))
    print("COOKIES", sorted(getattr(c, "cookies", {}).keys()) if hasattr(c,"cookies") else "?")
    for m in (c.list_models() if hasattr(c,"list_models") else []) or []: print("MODEL", m)
asyncio.run(main())
