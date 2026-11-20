"""Firefox oturumundaki Google hesaplarını /u/N/ indeksleriyle listeler."""
import asyncio, re, sys
from curl_cffi.requests import AsyncSession
sys.path.insert(0, "."); from ffcookie import oku
async def main():
    ck = oku(sys.argv[1] if len(sys.argv) > 1 else "ztjp9him.default-release")  # python hesap_bul.py <firefox profil klasoru>
    async with AsyncSession(impersonate="chrome") as s:
        for n, v, h in ck: s.cookies.set(n, v, domain=h)
        for i in range(10):
            r = await s.get(f"https://gemini.google.com/u/{i}/app", allow_redirects=True)
            m = re.search(r'"oPEP7c":"([^"]+)"', r.text); tok = '"SNlM0e"' in r.text
            print(i, r.status_code, str(r.url)[:60], m.group(1) if m else None, "token" if tok else "-")
            if not m: break
asyncio.run(main())
