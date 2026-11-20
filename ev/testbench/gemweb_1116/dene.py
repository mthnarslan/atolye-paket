import asyncio, json, sys
from gemini_webapi import GeminiClient
d = json.load(open("hesaplar/hesap1.json", encoding="utf-8-sig"))
async def main():
    c = GeminiClient(d.get("psid") or d["__Secure-1PSID"], d.get("psidts") or d.get("__Secure-1PSIDTS"), verbose=True)
    await c.init(timeout=120, auto_close=False, auto_refresh=True)
    print("durum1", c.account_status)
    r = await c.generate_content("Reply with exactly: OK 7", model="gemini-flash", temporary=True); print("metin:", r.text)
    print("durum2", c.account_status)
    r = await c.generate_content("Language spoken and speaker gender, one line.", files=[sys.argv[1]], model="gemini-flash", temporary=(sys.argv[2]=="1")); print("ses:", r.text)
asyncio.run(main())
