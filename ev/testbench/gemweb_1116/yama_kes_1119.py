import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119i"))


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)


# 11-19 GAIATRACE 2. test: ZAMAN=180 iken TimeoutError'lar 286-434 sn surdu: py3.12 wait_for iptal edilen
# kutuphane gorevinin (toparlanma dongusu) bitmesini bekliyor, hesap o sure tutuluyor. Gorevi birak, bekleme.
rep('def kredi(u):\n',
    'async def _sinirli(coro, sure):\n'
    '    t = asyncio.ensure_future(coro)\n'
    '    done, _ = await asyncio.wait({t}, timeout=sure)\n'
    '    if t in done: return t.result()\n'
    '    t.cancel(); t.add_done_callback(lambda f: f.cancelled() or f.exception())  # arkada bitsin, hata yutulsun\n'
    '    raise TimeoutError(f"{sure:.0f} sn")\n\n\n'
    'def kredi(u):\n')
rep('r = await asyncio.wait_for(cli.generate_content(', 'r = await _sinirli(cli.generate_content(')
# yetim gorevin sonraki close'u ayni hesaptaki yeni istegi dusurmesin: hesap mesgulken hic kapatma
rep('a is not None and a.cli is self and a.aktif > 1', 'a is not None and a.aktif > 1')
# timeout hiz siniri degil: kapasiteyi 1'e indirmesin (yalniz 1095/1013/1100); geri cikis 20 yerine 8 basari
rep('a.kap = 1 if gecici else a.kap;', 'a.kap = 1 if (gecici and "error code" in str(e)) else a.kap;')
rep('os.environ.get("GEMWEB_KAP_SERI", 20)', 'os.environ.get("GEMWEB_KAP_SERI", 8)')
p.write_text(s, encoding="utf-8"); print("ok")
