import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119d"))


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)


# 11-19 olcum: 8 hesap onceki istek bitince ~5 sn icinde yeni istek alirsa 1095 veriyor, 60 sn sonra calisiyor; u0/p1 5 sn araliga dayaniyor.
# Hesap basina aralik ogren: gecici hatada aralik ikiye katlanir (30..ARALIK_UST), basarida yavasca kisalir; secim en erken hazir olan hesabi alir.
rep('SOGUMA_GECICI = float(os.environ.get("GEMWEB_SOGUMA_GECICI", 60))',
    'SOGUMA_GECICI = float(os.environ.get("GEMWEB_SOGUMA_GECICI", 60)); ARALIK_UST = float(os.environ.get("GEMWEB_ARALIK_UST", 90))')
rep('        s.ok = s.hata = 0; s.son = 0.0; s.dinlen = 0.0;',
    '        s.ok = s.hata = 0; s.son = 0.0; s.dinlen = 0.0; s.aralik = ARALIK;')
rep('    return min(c, key=lambda a: a.son) if c else None',
    '    return min(c, key=lambda a: a.son + a.aralik) if c else None')
rep('            bekle = a.son + ARALIK - time.time()',
    '            bekle = a.son + a.aralik - time.time()')
rep('                a.ok += 1; a.son = time.time(); a.durum = "hazır"\n',
    '                a.ok += 1; a.son = time.time(); a.durum = "hazır"; a.aralik = max(ARALIK, a.aralik * 0.85)\n')
rep('a.dinlen = time.time() + (SOGUMA_GECICI if gecici else SOGUMA);',
    'a.aralik = min(ARALIK_UST, max(30.0, a.aralik * 2)) if gecici else a.aralik; a.dinlen = time.time() + (a.aralik if gecici else SOGUMA);')
rep('"ok": a.ok, "hata": a.hata,', '"ok": a.ok, "hata": a.hata, "aralik": round(a.aralik),')
p.write_text(s, encoding="utf-8"); print("ok")
