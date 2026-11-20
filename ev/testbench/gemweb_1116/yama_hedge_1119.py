import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119hedge"))


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)


# 11-19 17:50 olcum: son 300 denemede 19 zaman asimi (180 sn), ikinci kol yalniz 1 kez acildi.
# Sebep: kol 45. sn'de TEK kez bakiyordu; o an bos hesap yoksa (yuk altinda hep) bir daha bakmadan 180 sn bekliyordu.
# Saat de istegin sirada bekledigi sureyi sayiyordu. Yeni: saat hesap uretmeye basladigi anda baslar,
# 45 sn'den sonra 2 sn'de bir bos hesap aranir; ikinci kol sirada en one gecer (eski istek).
rep('''    denenen = set(); t1 = asyncio.create_task(_sor(prompt, files, model, yuksek, req, denenen, 1))
    done, _ = await asyncio.wait({t1}, timeout=HEDGE)
    if done or secim() is None: return await t1  # bos hesap yoksa ikinci kol acma: baskasinin kapasitesini calma
    t2 = asyncio.create_task(_sor(prompt, files, model, yuksek, req, denenen, 2)); kalan = {t1, t2}; ilk_hata = None''',
'''    denenen = set(); iz = {"bas": None}; t1 = asyncio.create_task(_sor(prompt, files, model, yuksek, req, denenen, 1, iz))
    while True:  # ilk kol HEDGE sn uretip donmediyse, bos hesap cikinca ikinci kol (bos hesap yoksa baskasinin kapasitesini calma)
        done, _ = await asyncio.wait({t1}, timeout=2)
        if done: return await t1
        if iz["bas"] and time.time() - iz["bas"] >= HEDGE and secim(denenen) is not None: break
    t2 = asyncio.create_task(_sor(prompt, files, model, yuksek, req, denenen, 2, None, True)); kalan = {t1, t2}; ilk_hata = None''')
rep('''async def _sor(prompt, files, model, yuksek, req=None, denenen=None, kol=1):
    b = _Bilet(); SIRA.append(b)
    try: return await _sor_ic(b, prompt, files, model, yuksek, req, denenen, kol)''',
'''async def _sor(prompt, files, model, yuksek, req=None, denenen=None, kol=1, iz=None, onde=False):
    b = _Bilet(); SIRA.insert(0, b) if onde else SIRA.append(b)
    try: return await _sor_ic(b, prompt, files, model, yuksek, req, denenen, kol, iz)''')
rep('async def _sor_ic(b, prompt, files, model, yuksek, req=None, denenen=None, kol=1):',
    'async def _sor_ic(b, prompt, files, model, yuksek, req=None, denenen=None, kol=1, iz=None):')
rep('''                authuser.AU.set(int(a.d.get("u", 0))); cli = await asyncio.wait_for(a.baglan(), BAGLAN); a.durum = "çalışıyor"''',
'''                authuser.AU.set(int(a.d.get("u", 0))); cli = await asyncio.wait_for(a.baglan(), BAGLAN); a.durum = "çalışıyor"
                if iz is not None: iz["bas"] = time.time()''')
# Panel: eski hata kartta durmasin (kullanici 11-19: "hata guncel degilse gozukmesin"). Basari hatayi siler;
# dinlenmeyen hesapta 10 dk'dan eski hata gosterilmez.
rep('a.ok += 1; a.son = time.time(); a.durum = "hazır";', 'a.ok += 1; a.son = time.time(); a.durum = "hazır"; a.son_hata = "";')
rep('a.son_hata = f"{type(e).__name__}: {str(e)[:160]}"\n', 'a.son_hata = f"{type(e).__name__}: {str(e)[:160]}"; a.son_hata_t = time.time()\n')
rep('"son_hata": a.son_hata,', '"son_hata": a.son_hata if (a.dinlen > time.time() or a.durum == "bağlanamadı" or time.time() - getattr(a, "son_hata_t", 0) < 600) else "",')
p.write_text(s, encoding="utf-8"); print("ok")
