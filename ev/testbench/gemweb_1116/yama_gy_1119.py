import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119k"))


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)


# 11-19 test 4: zaman asimi yalniz gorsel+high'ta (%30-50, 11:50'den beri), hesap/IP/kredi bagi yok -> Gemini tarafi takilma.
# Takilan istek 180 yerine 120 sn'de kesilsin; yeniden deneme kuyrukta onde (bilet basta) baska hesapta baslar.
rep('ZAMAN = float(os.environ.get("GEMWEB_ZAMAN", 180));',
    'ZAMAN_GY = float(os.environ.get("GEMWEB_ZAMAN_GORSEL_YUKSEK", 120))\nZAMAN = float(os.environ.get("GEMWEB_ZAMAN", 180));')
rep('extended_thinking=yuksek), ZAMAN)', 'extended_thinking=yuksek), ZAMAN_GY if (files and yuksek) else ZAMAN)')
p.write_text(s, encoding="utf-8"); print("ok")
