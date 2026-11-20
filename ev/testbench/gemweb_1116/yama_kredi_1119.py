import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119g"))


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:60]); s = s.replace(a, b)


# 11-19 GAIATRACE: gorsel+high yukte 18 istek 180 sn'de TimeoutError; kutuphane watchdog 120 sn sessizlikten sonra
# temporary sohbette bulamayacagi cevabi geri cekmeye ugrasiyordu. Erken kes -> sunucu baska hesapta dener.
rep('KAP = int(os.environ.get("GEMWEB_HESAP_PARALEL", 2));',
    'WATCHDOG = float(os.environ.get("GEMWEB_WATCHDOG", 45)); KREDI_ALT = int(os.environ.get("GEMWEB_KREDI_ALT", 40))\n'
    'KAP = int(os.environ.get("GEMWEB_HESAP_PARALEL", 2));')
rep('auto_close=False, auto_refresh=False)', 'auto_close=False, auto_refresh=False, watchdog_timeout=WATCHDOG)')
rep('auto_close=False, auto_refresh=True)', 'auto_close=False, auto_refresh=True, watchdog_timeout=WATCHDOG)')
# 11-19: hesap basi 5 saatlik kredi 2400 (istek ~11); biten hesap reset'e kadar secilmez, en cok kredisi kalan once
rep('def secim(haric=()):\n',
    'def kalan5(a, now):\n'
    '    c = a.limit.get("current_5h") or {}; r = c.get("remaining_credits")\n'
    '    if not isinstance(r, int): return 10**6\n'
    '    try: bitis = datetime.datetime.fromisoformat(c["reset_at"]).timestamp()\n'
    '    except Exception: bitis = 0\n'
    '    return 10**6 if bitis and bitis <= now else r\n\n\n'
    'def secim(haric=()):\n')
rep('a.son + a.aralik <= now + 0.5]\n    return min(c, key=lambda a: a.son + a.aralik) if c else None',
    'a.son + a.aralik <= now + 0.5 and kalan5(a, now) >= KREDI_ALT]\n    return max(c, key=lambda a: kalan5(a, now)) if c else None')
rep('"kap": a.kap, "aktif": a.aktif,', '"kap": a.kap, "aktif": a.aktif, "kredi_5s": (a.limit.get("current_5h") or {}).get("remaining_credits"),')
if "import datetime" not in s and "\nimport datetime" not in s:
    s = "import datetime\n" + s
p.write_text(s, encoding="utf-8"); print("ok")
