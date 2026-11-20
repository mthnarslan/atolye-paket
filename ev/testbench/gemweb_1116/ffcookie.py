"""Firefox profilinden google.com çerezlerini okur (kopya üzerinden, kilit yok)."""
import os, pathlib, shutil, sqlite3, tempfile
def oku(profil):
    p = pathlib.Path(os.environ["APPDATA"]) / "Mozilla/Firefox/Profiles" / profil
    t = pathlib.Path(tempfile.mkdtemp(prefix="ffck_"))
    for ek in ("", "-wal"):
        if (p / f"cookies.sqlite{ek}").exists(): shutil.copy2(p / f"cookies.sqlite{ek}", t / f"cookies.sqlite{ek}")
    c = sqlite3.connect(t / "cookies.sqlite")
    r = c.execute("select name,value,host from moz_cookies where host in ('.google.com','google.com','.gemini.google.com','gemini.google.com')").fetchall()
    c.close(); shutil.rmtree(t, ignore_errors=True)
    return r
