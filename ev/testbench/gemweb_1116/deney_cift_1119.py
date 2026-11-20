"""11-19: ayni hesapta ayni anda 2 istek 1095 veriyor mu? Kullanim: python deney_cift_1119.py <tur> hesap1 hesap2 ..."""
import asyncio, json, sys, time, pathlib
W = pathlib.Path(__file__).parent; sys.path.insert(0, str(W))
import server

n = int(sys.argv[1]); adlar = sys.argv[2:]
BAG = ("You are a documentary script editor. " + "The film covers glaciers, fjords, ocean currents and the animals that depend on them. " * 25)[:2400]


async def bir(cli, ad, i, j):
    t = time.time()
    try:
        await asyncio.wait_for(cli.generate_content(BAG + f"\nTask {ad} {i}-{j}: write 5 numbered one-sentence narration lines.",
                                                    model="gemini-4-hydrogen", temporary=True, extended_thinking=True), 120); s = "ok"
    except Exception as e:
        s = f"{type(e).__name__}: {str(e)[:50]}"
    print(json.dumps({"hesap": ad[:3], "i": i, "j": j, "sn": round(time.time() - t, 1), "sonuc": s}), flush=True)
    return s


async def isci(ad):
    d = json.loads((W / "hesaplar" / f"{ad}.json").read_text(encoding="utf-8-sig"))
    a = server.Hesap(ad, d); server.authuser.AU.set(int(d.get("u", 0))); cli = await a.client()
    for i in range(n):
        await asyncio.gather(bir(cli, ad, i, 0), bir(cli, ad, i, 1))
        await asyncio.sleep(5)


async def main(): await asyncio.gather(*(isci(a) for a in adlar))
asyncio.run(main())
