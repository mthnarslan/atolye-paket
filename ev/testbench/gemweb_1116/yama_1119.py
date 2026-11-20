import pathlib
p = pathlib.Path(__file__).parent / "server.py"; s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)


rep('ZAMAN = float(os.environ.get("GEMWEB_ZAMAN", 180));',
    'SOGUMA_GECICI = float(os.environ.get("GEMWEB_SOGUMA_GECICI", 60))  # 11-19: 1095/1013 gecici Google hatasi ~%4 istekte, hesaba ozel degil; 15 dk dinlenme kapasiteyi eritiyordu\n'
    'GECICI = re.compile(r"error code: (1095|1013|1100)|temporary error|TimeoutError|ReadTimeout", re.I)\n'
    'ISTEK_LOG = pathlib.Path(__file__).parent / "istek.jsonl"\n'
    'ZAMAN = float(os.environ.get("GEMWEB_ZAMAN", 180));')
rep('async def sor(prompt, files, model, yuksek):\n    yukle();',
    'def kaydet(**k):\n'
    '    try:\n'
    '        with ISTEK_LOG.open("a", encoding="utf-8") as f: f.write(json.dumps({"t": time.strftime("%m-%d %H:%M:%S"), **k}, ensure_ascii=False) + "\\n")\n'
    '    except Exception: pass\n\n\n'
    'async def sor(prompt, files, model, yuksek, req=None):\n    yukle();')
rep('        a = secim()\n        if a is None or a.ad in denenen:',
    '        if req is not None and await req.is_disconnected(): raise RuntimeError("istemci ayrıldı")  # 11-19: istemci vazgeçince sunucu 600 sn boşuna deniyordu\n'
    '        a = secim()\n        if a is None or a.ad in denenen:')
rep('                a.ok += 1; a.son = time.time(); a.durum = "hazır"',
    '                a.ok += 1; a.son = time.time(); a.durum = "hazır"\n'
    '                kaydet(hesap=a.ad, sonuc="ok", sn=round(time.time() - t0, 1), model=model, yuksek=yuksek, dosya=len(files), uzunluk=len(prompt))')
rep('a.dinlen = time.time() + (SOGUMA_ZAMAN if isinstance(e, TimeoutError) or "error code: 1100" in str(e) else SOGUMA);',
    'gecici = bool(GECICI.search(f"{type(e).__name__} {e}")); a.dinlen = time.time() + (SOGUMA_GECICI if gecici else SOGUMA);\n'
    '                kaydet(hesap=a.ad, sonuc=f"{type(e).__name__}: {str(e)[:120]}", gecici=gecici, sn=round(time.time() - t0, 1), model=model, yuksek=yuksek, dosya=len(files), uzunluk=len(prompt))')
rep('files, model, yuksek)\n    except Exception as e: return UJSON',
    'files, model, yuksek, req)\n    except Exception as e: return UJSON')
p.write_text(s, encoding="utf-8"); print("ok")
