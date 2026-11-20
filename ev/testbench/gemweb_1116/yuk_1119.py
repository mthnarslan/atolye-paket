"""11-19 yuk testi: 60 istek, 10 paralel, gemweb.py uzerinden (diger oturumlarla ayni slot havuzu). 40 metin (hydrogen high, ~2500 karakter), 20 gorsel (hydrogen low)."""
import sys, time, json, concurrent.futures as cf
sys.path.insert(0, r"C:\Users\meteh\Kanallar")
import gemweb
IMG = [r"C:\Users\meteh\testbench\ab_1109\sb\dry\2QVuQ59cJdU\sheet_00.jpg", r"C:\Users\meteh\testbench\ab_1109\sb\dry\2QVuQ59cJdU\sheet_01.jpg"]
BAG = ("You are a documentary script editor. " + "The film covers glaciers, fjords, ocean currents and the animals that depend on them. " * 25)[:2400]


def is_(i):
    t = time.time()
    try:
        if i % 3 == 2:
            r = gemweb.sor("Describe what you see in this contact sheet in 3 short bullet points.", gorseller=[IMG[i % 2]], effort="low")
            tur = "gorsel"
        else:
            r = gemweb.sor(BAG + f"\nTask {i}: write 5 numbered one-sentence narration lines about fjord formation.", effort="high")
            tur = "metin"
        return {"i": i, "tur": tur, "ok": True, "sn": round(time.time() - t, 1), "uz": len(str(r))}
    except Exception as e:
        return {"i": i, "tur": "?", "ok": False, "sn": round(time.time() - t, 1), "hata": str(e)[:150]}


t0 = time.time(); R = []
with cf.ThreadPoolExecutor(10) as ex:
    for r in ex.map(is_, range(60)):
        R.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)
ok = [r for r in R if r["ok"]]; s = sorted(r["sn"] for r in ok)
print("OZET", json.dumps({"toplam": len(R), "ok": len(ok), "sure_sn": round(time.time() - t0), "medyan": s[len(s) // 2] if s else None,
                          "p90": s[int(len(s) * .9)] if s else None, "max": s[-1] if s else None, ">120sn": sum(x > 120 for x in s)}), flush=True)
