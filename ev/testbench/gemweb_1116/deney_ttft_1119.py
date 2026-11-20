"""11-19: basarili istekte ilk parca (TTFT) kac sn? 1095 oncesi akista hic veri gelmiyor (30 sn sessizlik).
TTFT kisaysa 'N sn sessizlik = baska hesaba gec' erken sinyal olur.
Kullanim: python deney_ttft_1119.py <adet> [dusun] hesap1 hesap2 ..."""
import asyncio, json, sys, time, pathlib
W = pathlib.Path(__file__).parent; sys.path.insert(0, str(W))
import server

n = int(sys.argv[1]); dusun = "dusun" in sys.argv; adlar = [a for a in sys.argv[2:] if a != "dusun"]
BAG = ("You are a documentary script editor. " + "The film covers glaciers, fjords, ocean currents and the animals that depend on them. " * 25)[:2400]


async def isci(ad):
    d = json.loads((W / "hesaplar" / f"{ad}.json").read_text(encoding="utf-8-sig"))
    a = server.Hesap(ad, d); server.authuser.AU.set(int(d.get("u", 0))); cli = await a.client()
    for i in range(n):
        t = time.time(); ilk = None; parca = 0
        try:
            async def akis():
                nonlocal ilk, parca
                async for _ in cli.generate_content_stream(BAG + f"\nTask {ad} {i}: write 5 numbered one-sentence narration lines.",
                                                           model="gemini-4-hydrogen", temporary=True, extended_thinking=dusun):
                    parca += 1
                    if ilk is None: ilk = round(time.time() - t, 1)
            await asyncio.wait_for(akis(), 120); s = "ok"
        except Exception as e:
            s = f"{type(e).__name__}: {str(e)[:60]}"; a.cli = None; cli = await a.client()
        print(json.dumps({"hesap": ad, "i": i, "ttft": ilk, "sn": round(time.time() - t, 1), "parca": parca, "sonuc": s}, ensure_ascii=False), flush=True)
        await asyncio.sleep(5)


async def main(): await asyncio.gather(*(isci(a) for a in adlar))
asyncio.run(main())
