"""Tum hatlarin (belgesel anim.py, SkullStudio, kanal betikleri) ortak G-Labs slotu.

Belgesel anim.py'deki _Slot ile ayni kilit dosyalari: Belgesel_Teslim/_slots/glabs<i>.lock
(msvcrt bayt kilidi; surec olunce Windows kilidi birakir). Her cagiran 0..N-1 dosyalarini
denedigi icin makinedeki toplam esZamanli G-Labs isi en buyuk N'yi asmaz.
N: GLABS_SLOTS ortam degiskeni, yoksa 15 (kullanici 2026-11-17 tavani; beyin/ben/glabs-15-paralel).
Yerel upscale (/api/upscale) hesap kotasi kullanmaz, bu slota girmez.

Kullanim:
    from glabs_slot import GLABS
    with GLABS:            # GLABS.local.index, GLABS.local.waited
        ... G-Labs istegi + durum sorgusu ...
"""
import os, threading, time
from pathlib import Path

DIR = Path(os.environ.get("DOCUMENTARY_SLOT_DIR", r"C:\Users\meteh\Belgesel_Teslim\_slots"))
TAVAN = 15


class Slot:
    def __init__(self, name, n):
        self.paths = [DIR / ("%s%d.lock" % (name, i)) for i in range(n)]
        self.local = threading.local()

    def __enter__(self):
        import msvcrt
        DIR.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        while True:
            for index, p in enumerate(self.paths):
                f = open(p, "a+b")
                try:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    self.local.f, self.local.index = f, index
                    self.local.waited = round(time.monotonic() - started, 1)
                    return self
                except OSError:
                    f.close()
            time.sleep(1)

    def __exit__(self, *a):
        import msvcrt
        f = self.local.f
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            f.close()


def slot_sayisi():
    return max(1, min(TAVAN, int(os.environ.get("GLABS_SLOTS", str(TAVAN)) or TAVAN)))


GLABS = Slot("glabs", slot_sayisi())


def dolu():
    """Su an kac glabs kilidi tutuluyor (pano/olcum icin)."""
    import msvcrt
    n = 0
    for i in range(TAVAN):
        p = DIR / ("glabs%d.lock" % i)
        if not p.exists():
            continue
        f = open(p, "a+b")
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            n += 1
        finally:
            f.close()
    return n
