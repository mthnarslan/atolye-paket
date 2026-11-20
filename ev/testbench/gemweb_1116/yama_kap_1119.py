import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119f"))


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)


# 11-19 olcum: saglikli hesap ayni anda 2 istegi 18/18 temiz bitirdi (7-15 sn); sunucu hesap basina 1 istekle ~20 istek/dk'da tikaniyordu.
# Hesap basina ogrenilen paralellik: KAP (2) ile baslar, gecici hatada 1'e iner, art arda KAP_SERI basaridan sonra bir artar.
rep('SOGUMA_GECICI = float(os.environ.get("GEMWEB_SOGUMA_GECICI", 60));',
    'KAP = int(os.environ.get("GEMWEB_HESAP_PARALEL", 2)); KAP_SERI = int(os.environ.get("GEMWEB_KAP_SERI", 20))\n'
    'SOGUMA_GECICI = float(os.environ.get("GEMWEB_SOGUMA_GECICI", 60));')
rep('s.aralik = ARALIK; s.durum = "bekliyor";',
    's.aralik = ARALIK; s.aktif = 0; s.kap = KAP; s.seri = 0; s.durum = "bekliyor";')
# baglanti olusturma tek seferde (iki istek ayni anda client() kurmasin)
rep('    async def client(s):\n        authuser.AU.set(int(s.d.get("u", 0)))\n',
    '    async def baglan(s):\n        async with s.lock: return await s.client()\n\n'
    '    async def client(s):\n        authuser.AU.set(int(s.d.get("u", 0)))\n')
rep('not (H / f"{k}.json").exists() and not a.lock.locked()]', 'not (H / f"{k}.json").exists() and a.aktif == 0]')
rep('a.dinlen <= now and not a.lock.locked() and a.ad not in haric', 'a.dinlen <= now and a.aktif < a.kap and a.ad not in haric')
rep('        async with a.lock:\n            bekle = a.son + a.aralik - time.time()',
    '        async with _Tut(a):\n            bekle = a.son + a.aralik - time.time()')
rep('cli = await asyncio.wait_for(a.client(), BAGLAN)', 'cli = await asyncio.wait_for(a.baglan(), BAGLAN)')
rep('a.aralik = max(ARALIK, a.aralik * 0.85)\n',
    'a.aralik = max(ARALIK, a.aralik * 0.85); a.seri += 1\n'
    '                if a.seri >= KAP_SERI and a.kap < KAP: a.kap += 1; a.seri = 0\n')
rep('a.aralik = min(ARALIK_UST, max(30.0, a.aralik * 2)) if gecici else a.aralik;',
    'a.aralik = min(ARALIK_UST, max(30.0, a.aralik * 2)) if gecici else a.aralik; a.kap = 1 if gecici else a.kap; a.seri = 0;')
rep('SIRA = []  #', 'class _Tut:\n    def __init__(s, a): s.a = a\n    async def __aenter__(s): s.a.aktif += 1\n    async def __aexit__(s, *e): s.a.aktif -= 1\n\n\nSIRA = []  #')
rep('"ok": a.ok, "hata": a.hata, "aralik": round(a.aralik),', '"ok": a.ok, "hata": a.hata, "aralik": round(a.aralik), "kap": a.kap, "aktif": a.aktif,')
p.write_text(s, encoding="utf-8"); print("ok")
