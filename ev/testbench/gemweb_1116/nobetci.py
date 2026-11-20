"""gemweb sunucusu coker/kapanirsa yeniden baslatir (11-19). Gece kimse yokken tum kanallarin LLM'i durmasin.
Kullanim: .venv\\Scripts\\python.exe nobetci.py   (server.py'yi alt surec olarak kosar; loglar Kanallar\\bekci_log\\gemweb_*.log)
Durdurmak: bu sureci oldur (alt sureci de kapatir)."""
import subprocess, sys, time, pathlib, datetime

W = pathlib.Path(__file__).parent
LOG = pathlib.Path(r"C:\Users\meteh\Kanallar\bekci_log")
olumler = []
while True:
    with open(LOG / "gemweb_out.log", "ab") as o, open(LOG / "gemweb_err.log", "ab") as e:
        p = subprocess.Popen([sys.executable, str(W / "server.py")], cwd=W, stdout=o, stderr=e)
        try:
            kod = p.wait()
        except KeyboardInterrupt:
            p.terminate(); raise
    now = time.time(); olumler = [t for t in olumler if now - t < 600] + [now]
    bekle = 5 if len(olumler) < 3 else 120  # 10 dk'da 3 olum: dongude kirma, yavasla
    with open(LOG / "gemweb_nobetci.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%m-%d %H:%M:%S} server.py cikti kod={kod}; {bekle} sn sonra yeniden\n")
    time.sleep(bekle)
