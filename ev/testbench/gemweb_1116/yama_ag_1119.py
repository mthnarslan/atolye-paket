import pathlib, shutil
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")
shutil.copy(p, p.with_name("server.py.bak-1119ag"))


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)


# 11-19 14:20 ve 14:40: makinenin interneti koptu (torch/HF indirmeleri hatti doldurdu), 81 istek DNS/proxy hatasi aldi.
# Eskiden her hesap tek tek hata yazip 30 sn dinleniyor, istek "tum hesaplar hata verdi" ile dusuyordu.
# Yeni: 30 sn icinde >=3 farkli hesapta ag hatasi = makine capi kesinti: hesap cezalandirilmaz, istek dusmez, herkes 10 sn bekleyip yeniden dener.
rep('ISTEK_LOG = pathlib.Path(__file__).parent / "istek.jsonl"',
    'ISTEK_LOG = pathlib.Path(__file__).parent / "istek.jsonl"\nAG_SON = deque(maxlen=50); AG_DUR = [0.0]; AG_ESIK = int(os.environ.get("GEMWEB_AG_ESIK", 3))')
rep('        a = secim(denenen)\n        if a is None:',
    '        if time.time() < AG_DUR[0]: await asyncio.sleep(0.5); continue  # makine capi ag kesintisi: bekle, hesap yakma\n        a = secim(denenen)\n        if a is None:')
rep('                a.hata += 1; a.son = time.time(); ag = bool(AG.search(f"{type(e).__name__} {e}"));',
    '                if AG.search(f"{type(e).__name__} {e}"):\n'
    '                    AG_SON.append((time.time(), a.ad)); son30 = {n for t, n in AG_SON if time.time() - t < 30}\n'
    '                    if len(son30) >= AG_ESIK:\n'
    '                        AG_DUR[0] = time.time() + 10; a.son = time.time(); a.durum = "hazır"; a.cli = None\n'
    '                        kaydet(hesap=a.ad, sonuc=f"ag kesik (bekleniyor): {type(e).__name__}: {str(e)[:80]}", kol=kol, sn=round(time.time() - t0, 1), model=model, yuksek=yuksek, dosya=len(files))\n'
    '                        LOG.appendleft({"t": time.strftime("%H:%M:%S"), "hesap": a.ad, "sonuc": "ağ kesik, 10 sn bekleniyor", "sn": round(time.time() - t0, 1), "model": model, "dosya": len(files), "kredi": None})\n'
    '                        continue\n'
    '                a.hata += 1; a.son = time.time(); ag = bool(AG.search(f"{type(e).__name__} {e}"));')
# 11-19 14:51 temiz test: istemci medyan 75 sn, sunucu ok medyan 16 sn -> fark kuyruk. Sebep: TimeoutError (gorsel+high takilmasi, Gemini yuku)
# 1095 gibi sayilip aralik x2 (30-90 sn) ve kap 1'de kaliyordu; 14:00'ten beri 82 zaman asimi tum hesaplarin araligini 21-68 sn'ye sisirdi.
# Yeni: zaman asimi araligi buyutmez, hesap 10 sn dinlenir; aralik yalniz 1095/1013/1100'de buyur.
rep('a.aralik = min(ARALIK_UST, max(30.0, a.aralik * 2)) if (gecici and not ag) else a.aralik;',
    'zaman = "TimeoutError" in type(e).__name__ or "ReadTimeout" in f"{e}"; a.aralik = min(ARALIK_UST, max(30.0, a.aralik * 2)) if (gecici and not ag and not zaman) else a.aralik;')
rep('(min(SOGUMA_GECICI, 30.0) if ag else a.aralik if gecici else SOGUMA)',
    '(min(SOGUMA_GECICI, 30.0) if ag else 10.0 if zaman else a.aralik if gecici else SOGUMA)')
p.write_text(s, encoding="utf-8"); print("ok")
