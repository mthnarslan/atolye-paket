import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119h"))


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)


# 11-19 olcum: kutuphane watchdog'u takilan akista self.close() ile TUM http oturumunu kapatiyor; ayni hesapta
# ikinci istek varsa o da dusuyor (0,5-1,2 sn'de "HTTP Error 0", "connection lost"). Takilan akis break ile zaten kapanir.
rep('def kredi(u):\n',
    '_SAHIP = {}; _asil_close = GeminiClient.close\n\n\n'
    'async def _close(self, delay=0):\n'
    '    a = _SAHIP.get(id(self))\n'
    '    if not delay and a is not None and a.cli is self and a.aktif > 1: return  # baska istek bu oturumda: kapatma\n'
    '    return await _asil_close(self, delay)\n'
    'GeminiClient.close = _close\n\n\n'
    'def kredi(u):\n')
rep('            s.cli = c; s.limit = kredi(c.usage_info)', '            s.cli = c; _SAHIP[id(c)] = s; s.limit = kredi(c.usage_info)')
p.write_text(s, encoding="utf-8"); print("ok")
