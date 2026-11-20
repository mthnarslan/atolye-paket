"""11-19 deney: yavas hesapta 1095 neden? Tek hesap, art arda (5 sn ara) istek.
Kullanim: python deney_temp_1119.py <hesap_adi> <temp 0|1> <adet> [kota] [dusun] [uzun]"""
import asyncio, json, sys, time, pathlib
W = pathlib.Path(__file__).parent; sys.path.insert(0, str(W))
import server  # yamalar + authuser kurulu gelir
import os
if os.environ.get("DEBUG"):
    from gemini_webapi import set_log_level; set_log_level("DEBUG")

ad, temp, n = sys.argv[1], sys.argv[2] == "1", int(sys.argv[3]); ek = set(sys.argv[4:])
BAG = ("You are a documentary script editor. " + "The film covers glaciers, fjords, ocean currents and the animals that depend on them. " * 25)[:2400]


async def main():
    d = json.loads((W / "hesaplar" / f"{ad}.json").read_text(encoding="utf-8-sig"))
    a = server.Hesap(ad, d); cli = await a.client()
    for i in range(n):
        server.authuser.AU.set(int(d.get("u", 0))); t = time.time()
        p = BAG + f"\nTask {i}: write 5 numbered one-sentence narration lines about fjord formation." if "uzun" in ek else f"Say one short sentence about fjords. ({i})"
        try:
            await asyncio.wait_for(cli.generate_content(p, model=os.environ.get("M","gemini-4-hydrogen"), temporary=temp, extended_thinking="dusun" in ek), 120)
            s = "ok"
            if "kota" in ek: await cli._fetch_quota()
        except Exception as e:
            s = f"{type(e).__name__}: {str(e)[:90]}"; a.cli = None; cli = await a.client()
        print(json.dumps({"hesap": ad, "i": i, "t": time.strftime("%H:%M:%S"), "sn": round(time.time() - t, 1), "sonuc": s, "ek": sorted(ek)}, ensure_ascii=False), flush=True)
        await asyncio.sleep(5)

asyncio.run(main())
