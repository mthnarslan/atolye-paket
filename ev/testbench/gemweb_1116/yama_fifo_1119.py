import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119e"))


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)


# 11-19 yuk testi: istemci p90 118 / max 345 sn iken sunucu kolu max 57 sn -> bekleme sirada.
# 1) dosyasi silinen hesap ACC'den duser (gecici deney dosyasi p3'un kopyasi olarak kalmisti)
rep('        if f.stem not in ACC: ACC[f.stem] = Hesap(f.stem, json.loads(f.read_text(encoding="utf-8-sig")))\n',
    '        if f.stem not in ACC: ACC[f.stem] = Hesap(f.stem, json.loads(f.read_text(encoding="utf-8-sig")))\n'
    '    for k in [k for k, a in ACC.items() if not (H / f"{k}.json").exists() and not a.lock.locked()]: ACC.pop(k, None)\n')
# 2) secim yalniz HAZIR hesabi verir (aralik dolmus); denenen hesaplar disarida. Eskiden 90 sn araligi olan hesabi kilitleyip uyuyordu.
rep('def secim():\n    now = time.time(); c = [a for a in ACC.values() if a.dinlen <= now and not a.lock.locked()]\n',
    'def secim(haric=()):\n    now = time.time(); c = [a for a in ACC.values() if a.dinlen <= now and not a.lock.locked() and a.ad not in haric and a.son + a.aralik <= now + 0.5]\n')
# 3) FIFO: bekleyen istekler gelis sirasiyla hesap alir; onundeki istek hesap alamiyorsa (takili) sira atlanir.
rep('async def _sor(prompt, files, model, yuksek, req=None, denenen=None, kol=1):\n'
    '    yukle(); t_end = time.time() + 600; denenen = set() if denenen is None else denenen; model_hata = 0; tazelenen = set()\n'
    '    while time.time() < t_end:\n',
    'SIRA = []  # 11-19: bekleyen istek biletleri, gelis sirasiyla (eskiden 2 sn yoklama: sonra gelen one geciyordu)\n\n\n'
    'class _Bilet:\n    def __init__(s): s.takili = False\n\n\n'
    'async def _sor(prompt, files, model, yuksek, req=None, denenen=None, kol=1):\n'
    '    b = _Bilet(); SIRA.append(b)\n'
    '    try: return await _sor_ic(b, prompt, files, model, yuksek, req, denenen, kol)\n'
    '    finally:\n'
    '        if b in SIRA: SIRA.remove(b)\n\n\n'
    'async def _sor_ic(b, prompt, files, model, yuksek, req=None, denenen=None, kol=1):\n'
    '    yukle(); t_end = time.time() + 600; denenen = set() if denenen is None else denenen; model_hata = 0; tazelenen = set()\n'
    '    while time.time() < t_end:\n')
rep('        a = secim()\n'
    '        if a is None or a.ad in denenen:\n'
    '            if len(denenen) >= max(1, len(ACC)): raise RuntimeError("tüm hesaplar hata verdi")\n'
    '            await asyncio.sleep(2); continue\n'
    '        async with a.lock:\n',
    '        a = secim(denenen)\n'
    '        if a is None:\n'
    '            if len(denenen) >= max(1, len(ACC)): raise RuntimeError("tüm hesaplar hata verdi")\n'
    '            b.takili = True; await asyncio.sleep(0.25); continue\n'
    '        if any(not x.takili for x in SIRA[:SIRA.index(b)]): b.takili = False; await asyncio.sleep(0.25); continue  # sira onumdekinde\n'
    '        b.takili = True  # hesap aldim: arkadakileri tutma\n'
    '        async with a.lock:\n')
p.write_text(s, encoding="utf-8"); print("ok")
