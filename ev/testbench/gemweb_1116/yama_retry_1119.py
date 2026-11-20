import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119c"))


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)


# 1) kutuphane ici yeniden deneme: @running(retry=5) her APIError'da (1095 dahil) ayni hesapta 5+10+15+20+25 sn bekleyip tekrar dener (~90 sn kayip).
#    1'e indir: hizli dussun, sunucu baska hesaba gecsin.
rep('    async for x in _gen0(self, *a, req_file_data=req_file_data, **k): yield x',
    '    k.setdefault("current_retry", int(os.environ.get("GEMWEB_KUTUPHANE_DENEME", 1)))  # 11-19: kutuphane retry=5 1095te ayni hesapta 75 sn uyuyordu\n'
    '    async for x in _gen0(self, *a, req_file_data=req_file_data, **k): yield x')
# 2) aktif modeller: kullanici 11-19 hydrogen + neon (karbon kilitli, argon yok); varsayilan hydrogen (flash-lite istenmiyor)
rep('VARSAYILAN_MODEL =os.environ.get("GEMWEB_MODEL", "gemini-flash-lite")',
    'VARSAYILAN_MODEL =os.environ.get("GEMWEB_MODEL", "gemini-4-hydrogen")\n'
    'IZINLI = [m for m in os.environ.get("GEMWEB_MODELLER", "gemini-4-hydrogen,gemini-neon").split(",") if m]  # 11-19 kullanici: aktif modeller')
rep('    yukle(); bilinen = {m for a in ACC.values() for m in a.modeller}\n',
    '    yukle(); bilinen = {m for a in ACC.values() for m in a.modeller}; bilinen = (bilinen & set(IZINLI)) if IZINLI and bilinen else bilinen\n')
rep('    ms = sorted({m for a in ACC.values() for m in a.modeller} or {VARSAYILAN_MODEL})',
    '    ms = sorted({m for a in ACC.values() for m in a.modeller} or {VARSAYILAN_MODEL}); ms = [m for m in ms if not IZINLI or m in IZINLI] or ms')
p.write_text(s, encoding="utf-8"); print("ok")
