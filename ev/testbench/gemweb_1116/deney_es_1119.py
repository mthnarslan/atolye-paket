"""11-19 deney: ayni surecte birden cok hesap ESZAMANLI calisinca 1095 cikiyor mu? (tek hesap tek surecte 24/24 temiz)
Kullanim: python deney_es_1119.py <adet> hesap1 hesap2 ..."""
import asyncio, json, sys, time, pathlib
W = pathlib.Path(__file__).parent; sys.path.insert(0, str(W))
import server

n = int(sys.argv[1]); adlar = sys.argv[2:]
BAG = ("You are a documentary script editor. " + "The film covers glaciers, fjords, ocean currents and the animals that depend on them. " * 25)[:2400]


async def isci(ad):
    d = json.loads((W / "hesaplar" / f"{ad}.json").read_text(encoding="utf-8-sig"))
    a = server.Hesap(ad, d); server.authuser.AU.set(int(d.get("u", 0))); cli = await a.client()
    for i in range(n):
        t = time.time()
        try:
            await asyncio.wait_for(cli.generate_content(BAG + f"\nTask {ad} {i}: write 5 numbered one-sentence narration lines.", model="gemini-4-hydrogen", temporary=True), 120); s = "ok"
        except Exception as e:
            s = f"{type(e).__name__}: {str(e)[:90]}"; a.cli = None; cli = await a.client()
        print(json.dumps({"hesap": ad, "i": i, "t": time.strftime("%H:%M:%S"), "sn": round(time.time() - t, 1), "sonuc": s}, ensure_ascii=False), flush=True)
        await asyncio.sleep(5)


async def main(): await asyncio.gather(*(isci(a) for a in adlar))
asyncio.run(main())
