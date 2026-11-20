"""Gemini web (gemini.google.com oturumu) -> OpenAI uyumlu yerel sunucu + izleme paneli.
Hesaplar: hesaplar/<ad>.json
  {"firefox": "<profil klasörü>", "u": N}   -> çerezler her bağlanışta Firefox'tan taze okunur; u = gemini.google.com/u/N hesap indeksi
  "proxy": "socks5h://kullanici:sifre@ip:port"  (isteğe bağlı) -> bu hesabın TÜM istekleri bu proxy'den; Firefox profili de aynı proxy'yi kullanmalı
  {"psid": "...", "psidts": "..."}   -> elle çerez (tarayıcı yenileyince bozulur)
Çalıştır: .venv/Scripts/python.exe server.py   -> panel http://127.0.0.1:8790/   API http://127.0.0.1:8790/v1
Nazik kullanım: hesap başına aynı anda 1 istek, istekler arası en az ARALIK sn; hata alan hesap SOGUMA sn dinlenir.
reasoning_effort=high -> extended_thinking; diğer her şey düşük (varsayılan)."""
import asyncio, datetime, re, shutil, base64, json, os, pathlib, sys, tempfile, time, uuid
from collections import deque
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from gemini_webapi import GeminiClient
import mimetypes

# 11-18: kütüphane (2.1.1) yüklenen dosyayı [[url], ad] diye gönderiyor; ses/video türü (4/2 + mime) yoksa Gemini dosyayı duymuyor ("CANNOT").
# Biçim upstream PR #179'dan (birleşmedi): [[url, tür, None, mime], ad]. Resim zaten çalışıyor -> yalnız ses/video değişir.
_TUR = {"audio", "video"}
def _av(ad): return (mimetypes.guess_type(ad)[0] or "").split("/")[0] in _TUR
_gen0 = GeminiClient._generate
async def _gen(self, *a, req_file_data=None, **k):
    # 11-18: web arayüzünden yakalanan biçim (build 20261117): dosya girdisi [[url,None,1,mime],ad,None*6,[0]];
    # göndermeden önce PCck7e RPC'si ile dosya kaydedilir. GEMWEB_AV=1 ile açılır.
    if req_file_data and os.environ.get("GEMWEB_AV", "1") == "1" and any(_av(ad) for u, ad in req_file_data):
        y = [[[u[0], None, 1, mimetypes.guess_type(ad)[0] or "application/octet-stream"], ad, None, None, None, None, None, None, [0]] for u, ad in req_file_data]
        # web önce ProcessFile ile dosyayı işletir (yanıt [null,null,1,[uuid]]); bu olmadan ses duyulmuyor
        try:
            from gemini_webapi.constants import Headers as _H
            n = authuser.AU.get(); base = "https://gemini.google.com/" + (f"u/{n}/" if n else "")
            prm = {"hl": self.language, "_reqid": self._reqid, "rt": "c"}; self._reqid += 100000
            if self.build_label: prm["bl"] = self.build_label
            if self.session_id: prm["f.sid"] = self.session_id
            inner = json.dumps([y, None, 1, ["en"]], separators=(",", ":"))
            z = []
            for i in range(len(y)):
                r = await self._live_client.post(base + "_/BardChatUi/data/assistant.lamda.BardFrontendService/ProcessFile", params=prm,
                    headers={**_H.GEMINI.value, **_H.SAME_DOMAIN.value}, data={"f.req": json.dumps([None, json.dumps([y[i], None, 1, ["en"]], separators=(",", ":"))], separators=(",", ":")), "at": self.access_token or ""})
                m = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", r.text)
                if not m: print("ProcessFile uuid yok", r.status_code, r.text[:160].replace(chr(10), " "), flush=True)
                u0, _, _, mt = y[i][0]; tur = {"audio": 4, "video": 2}.get(mt.split("/")[0])
                # web (processSession protobuf, 11-18): dosya = [[url, tür(ses 4/video 2), None, mime, uuid], ad, None*6, [0]]
                z.append([[u0, tur, None, mt] + ([m.group(0)] if m else []), y[i][1], None, None, None, None, None, None, [0]])
            await asyncio.sleep(float(os.environ.get("GEMWEB_AVBEKLE", "8"))); req_file_data = z; print("AV dosya", json.dumps(z)[:300], flush=True)
        except Exception as e: print("ProcessFile hata", type(e).__name__, str(e)[:160], flush=True); req_file_data = y
    k.setdefault("current_retry", int(os.environ.get("GEMWEB_KUTUPHANE_DENEME", 1)))  # 11-19: kutuphane retry=5 1095te ayni hesapta 75 sn uyuyordu
    async for x in _gen0(self, *a, req_file_data=req_file_data, **k): yield x
GeminiClient._generate = _gen

import gemini_webapi.client as _gwc
from gemini_webapi.constants import Headers as _Hd
_up0 = _gwc.upload_file
async def _up(file, client, push_id, filename=None, verbose=False):
    # ses/video: web arayüzünün resumable yolu (X-Tenant-Id: bard-storage); resim eski yolda kalır
    p = pathlib.Path(file); ad = filename or p.name
    if os.environ.get("GEMWEB_AV", "1") != "1" or not _av(ad): return await _up0(file, client=client, push_id=push_id, filename=filename, verbose=verbose)
    data = p.read_bytes(); h = {**_Hd.REFERER.value, "push-id": push_id, "x-tenant-id": "bard-storage", **({"x-goog-authuser": str(authuser.AU.get())} if os.environ.get("GEMWEB_AUHDR", "0") == "1" else {})}
    n = authuser.AU.get(); r = await client.post("https://push.clients6.google.com/upload/" + (f"?authuser={n}" if n and os.environ.get("GEMWEB_AUQ", "1") == "1" else ""), headers={**h, "x-goog-upload-protocol": "resumable", "x-goog-upload-command": "start", "x-goog-upload-header-content-length": str(len(data)), "content-type": "application/x-www-form-urlencoded;charset=utf-8"}, data=f"File name: {ad}")
    url = r.headers.get("x-goog-upload-url"); r.raise_for_status()
    r2 = await client.post(url, headers={**h, "x-goog-upload-command": "upload, finalize", "x-goog-upload-offset": "0", "content-type": "application/x-www-form-urlencoded;charset=utf-8"}, data=data)
    r2.raise_for_status(); return r2.text
_gwc.upload_file = _up

W = pathlib.Path(__file__).parent; sys.path.insert(0, str(W)); H = W / "hesaplar"; H.mkdir(exist_ok=True)
from ffcookie import oku
import authuser; authuser.kur()

ARALIK = float(os.environ.get("GEMWEB_ARALIK", 5)); SOGUMA = float(os.environ.get("GEMWEB_SOGUMA", 900))
WATCHDOG = float(os.environ.get("GEMWEB_WATCHDOG", 45)); KREDI_ALT = int(os.environ.get("GEMWEB_KREDI_ALT", 40))
KAP = int(os.environ.get("GEMWEB_HESAP_PARALEL", 2)); KAP_SERI = int(os.environ.get("GEMWEB_KAP_SERI", 8))
SOGUMA_GECICI = float(os.environ.get("GEMWEB_SOGUMA_GECICI", 60)); ARALIK_UST = float(os.environ.get("GEMWEB_ARALIK_UST", 90))  # 11-19: 1095/1013 gecici Google hatasi ~%4 istekte, hesaba ozel degil; 15 dk dinlenme kapasiteyi eritiyordu
AG = re.compile(r"ConnectionError|SSLError|DNSError|curl: \((6|7|28|35|52|55|56)\)|while connecting|Connection (was )?reset|Connection closed", re.I)
GECICI = re.compile(r"error code: (1095|1013|1100)|temporary error|TimeoutError|ReadTimeout", re.I)
ISTEK_LOG = pathlib.Path(__file__).parent / "istek.jsonl"
AG_SON = deque(maxlen=50); AG_DUR = [0.0]; AG_ESIK = int(os.environ.get("GEMWEB_AG_ESIK", 3))
HEDGE = float(os.environ.get("GEMWEB_HEDGE", 45))  # 11-19: 45 sn cevap yoksa bos hesapta ikinci kol; ilk donen kazanir (1095 ~90 sn sonra gelir, basarili p90 ~50 sn). 0 = kapali
ZAMAN_GY = float(os.environ.get("GEMWEB_ZAMAN_GORSEL_YUKSEK", 120))  # 11-19: 180->120: 40/40 684 sn (180de 15 dk bitmedi); 75 denendi: 39/40 685 sn, 1095 x14 -> 120 kaldi
ZAMAN = float(os.environ.get("GEMWEB_ZAMAN", 180)); BAGLAN = 90; SOGUMA_ZAMAN = 120  # zaman aşımı hesap hatası değil: kısa dinlenme  # tek istek üst sınırı (gemini-pro takılıyor)
VARSAYILAN_MODEL =os.environ.get("GEMWEB_MODEL", "gemini-4-hydrogen")
IZINLI = [m for m in os.environ.get("GEMWEB_MODELLER", "gemini-4-hydrogen,gemini-neon").split(",") if m]  # 11-19 kullanici: aktif modeller
HATA_METNI = re.compile(r"^\s*(I seem to be encountering an error|Something went wrong|I'm having a hard time fulfilling your request)", re.I)


class ModelHata(RuntimeError): pass
class BilinmeyenModel(ModelHata): pass


class UJSON(JSONResponse): media_type = "application/json; charset=utf-8"


app = FastAPI(default_response_class=UJSON); LOG = deque(maxlen=40); ACC = {}


_SAHIP = {}; _asil_close = GeminiClient.close


async def _close(self, delay=0):
    a = _SAHIP.get(id(self))
    if not delay and a is not None and a.aktif > 1: return  # baska istek bu oturumda: kapatma
    return await _asil_close(self, delay)
GeminiClient.close = _close


async def _sinirli(coro, sure):
    t = asyncio.ensure_future(coro)
    try: done, _ = await asyncio.wait({t}, timeout=sure)
    except asyncio.CancelledError: t.cancel(); raise  # diger kol kazandi: alt gorevi de birak
    if t in done: return t.result()
    t.cancel(); t.add_done_callback(lambda f: f.cancelled() or f.exception())  # arkada bitsin, hata yutulsun
    raise TimeoutError(f"{sure:.0f} sn")


def kredi(u):
    u = u or {}
    return {"current_5h": u.get("current_5h") or {}, "weekly": u.get("weekly") or {}, "tier": (u.get("tier") or {}).get("label")}


class Hesap:
    def __init__(s, ad, d):
        s.ad, s.d, s.cli, s.lock = ad, d, None, asyncio.Lock()
        s.ok = s.hata = 0; s.son = 0.0; s.dinlen = 0.0; s.aralik = ARALIK; s.aktif = 0; s.kap = KAP; s.seri = 0; s.durum = "bekliyor"; s.son_hata = ""; s.limit = {}; s.modeller = []

    async def baglan(s):
        async with s.lock: return await s.client()

    async def client(s):
        authuser.AU.set(int(s.d.get("u", 0)))
        if s.cli is None:
            s.durum = "bağlanıyor"
            if "firefox" in s.d:
                ck = oku(s.d["firefox"]); m = {n: v for n, v, h in ck}
                c = GeminiClient(m["__Secure-1PSID"], m.get("__Secure-1PSIDTS"), proxy=s.d.get("proxy"))
                for n, v, h in ck:
                    if n not in ("__Secure-1PSID", "__Secure-1PSIDTS"): c._cookies.set(n, v, domain=h)
                await c.init(timeout=120, auto_close=False, auto_refresh=False, watchdog_timeout=WATCHDOG)  # yenilemeyi Firefox yapar
            else:
                c = GeminiClient(s.d.get("psid") or s.d["__Secure-1PSID"], s.d.get("psidts") or s.d.get("__Secure-1PSIDTS"), proxy=s.d.get("proxy"))
                await c.init(timeout=120, auto_close=False, auto_refresh=True, watchdog_timeout=WATCHDOG)
            if c.account_status.name != "AVAILABLE": raise RuntimeError(f"hesap durumu {c.account_status.name}")
            s.cli = c; _SAHIP[id(c)] = s; s.limit = kredi(c.usage_info)
            s.modeller = [getattr(x, "model_name", str(x)) for x in (c.list_models() or [])]
            s.durum = "hazır"
        return s.cli


def yukle():
    for f in sorted(H.glob("*.json")):
        if f.stem not in ACC: ACC[f.stem] = Hesap(f.stem, json.loads(f.read_text(encoding="utf-8-sig")))
    for k in [k for k, a in ACC.items() if not (H / f"{k}.json").exists() and a.aktif == 0]: ACC.pop(k, None)


def kalan5(a, now):
    c = a.limit.get("current_5h") or {}; r = c.get("remaining_credits")
    if not isinstance(r, int): return 10**6
    try: bitis = datetime.datetime.fromisoformat(c["reset_at"]).timestamp()
    except Exception: bitis = 0
    return 10**6 if bitis and bitis <= now else r


def secim(haric=()):
    now = time.time(); c = [a for a in ACC.values() if a.dinlen <= now and a.aktif < a.kap and a.ad not in haric and a.son + a.aralik <= now + 0.5 and kalan5(a, now) >= KREDI_ALT]
    return max(c, key=lambda a: kalan5(a, now)) if c else None


def kaydet(**k):
    try:
        with ISTEK_LOG.open("a", encoding="utf-8") as f: f.write(json.dumps({"t": time.strftime("%m-%d %H:%M:%S"), **k}, ensure_ascii=False) + "\n")
    except Exception: pass


async def sor(prompt, files, model, yuksek, req=None):
    if HEDGE <= 0: return await _sor(prompt, files, model, yuksek, req)
    denenen = set(); iz = {"bas": None}; t1 = asyncio.create_task(_sor(prompt, files, model, yuksek, req, denenen, 1, iz))
    while True:  # ilk kol HEDGE sn uretip donmediyse, bos hesap cikinca ikinci kol (bos hesap yoksa baskasinin kapasitesini calma)
        done, _ = await asyncio.wait({t1}, timeout=2)
        if done: return await t1
        if iz["bas"] and time.time() - iz["bas"] >= HEDGE and secim(denenen | {iz["hesap"]}) is not None: denenen.add(iz["hesap"]); break  # ikinci kol ayni hesaba gitmesin
    t2 = asyncio.create_task(_sor(prompt, files, model, yuksek, req, denenen, 2, None, True)); kalan = {t1, t2}; ilk_hata = None
    try:
        while kalan:
            done, kalan = await asyncio.wait(kalan, return_when=asyncio.FIRST_COMPLETED)
            for t in done:
                if t.exception() is None: return t.result()
                ilk_hata = ilk_hata or t.exception()
        raise ilk_hata
    finally:
        for t in (t1, t2):
            if not t.done(): t.cancel()


class _Tut:
    def __init__(s, a): s.a = a
    async def __aenter__(s): s.a.aktif += 1
    async def __aexit__(s, *e): s.a.aktif -= 1


SIRA = []  # 11-19: bekleyen istek biletleri, gelis sirasiyla (eskiden 2 sn yoklama: sonra gelen one geciyordu)


class _Bilet:
    def __init__(s): s.takili = False


async def _sor(prompt, files, model, yuksek, req=None, denenen=None, kol=1, iz=None, onde=False):
    b = _Bilet(); SIRA.insert(0, b) if onde else SIRA.append(b)
    try: return await _sor_ic(b, prompt, files, model, yuksek, req, denenen, kol, iz)
    finally:
        if b in SIRA: SIRA.remove(b)


async def _sor_ic(b, prompt, files, model, yuksek, req=None, denenen=None, kol=1, iz=None):
    yukle(); t_end = time.time() + 600; denenen = set() if denenen is None else denenen; model_hata = 0; tazelenen = set()
    denenen.update(x.ad for x in ACC.values() if x.modeller and model not in x.modeller)  # 11-19: PRO olmayan hesap (yalniz 'otomatik') bu modeli tasimiyor: ona hic gitme
    while time.time() < t_end:
        if req is not None and await req.is_disconnected(): raise RuntimeError("istemci ayrıldı")  # 11-19: istemci vazgeçince sunucu 600 sn boşuna deniyordu
        if time.time() < AG_DUR[0]: await asyncio.sleep(0.5); continue  # makine capi ag kesintisi: bekle, hesap yakma
        a = secim(denenen)
        if a is None:
            if len(denenen) >= max(1, len(ACC)): raise RuntimeError("tüm hesaplar hata verdi")
            b.takili = True; await asyncio.sleep(0.25); continue
        if any(not x.takili for x in SIRA[:SIRA.index(b)]): b.takili = False; await asyncio.sleep(0.25); continue  # sira onumdekinde
        b.takili = True  # hesap aldim: arkadakileri tutma
        async with _Tut(a):
            bekle = a.son + a.aralik - time.time()
            if bekle > 0: a.durum = f"aralık {bekle:.0f} sn"; await asyncio.sleep(bekle)
            t0 = time.time()
            try:
                authuser.AU.set(int(a.d.get("u", 0))); cli = await asyncio.wait_for(a.baglan(), BAGLAN); a.durum = "çalışıyor"
                if iz is not None: iz["bas"] = time.time(); iz["hesap"] = a.ad
                k0 = (a.limit.get("weekly") or {}).get("remaining_credits")
                r = await _sinirli(cli.generate_content(prompt, files=files or None, model=model, temporary=True, extended_thinking=yuksek), ZAMAN_GY if (files and yuksek) else ZAMAN)
                try: await cli._fetch_quota(); a.limit = kredi(cli.usage_info)
                except Exception: pass
                k1 = (a.limit.get("weekly") or {}).get("remaining_credits")
                if HATA_METNI.search((r.text or "")[:300]):  # Gemini 200 ile hata cümlesi döndürdü: hesabı dinlendirme, başka hesapta dene
                    a.son = time.time(); a.durum = "hazır"; denenen.add(a.ad); model_hata += 1
                    LOG.appendleft({"t": time.strftime("%H:%M:%S"), "hesap": a.ad, "sonuc": "model hata metni: " + (r.text or "")[:80], "sn": round(time.time() - t0, 1),
                                    "model": model, "dosya": len(files), "kredi": None})
                    if model_hata >= 2: raise ModelHata(f"{model} bu isteği işleyemedi (2 hesapta hata metni): {(r.text or '')[:120]}")
                    continue
                a.ok += 1; a.son = time.time(); a.durum = "hazır"; a.son_hata = ""; a.aralik = max(ARALIK, a.aralik * 0.85); a.seri += 1
                if a.seri >= KAP_SERI and a.kap < KAP: a.kap += 1; a.seri = 0
                kaydet(hesap=a.ad, sonuc="ok", kol=kol, sn=round(time.time() - t0, 1), model=model, yuksek=yuksek, dosya=len(files), uzunluk=len(prompt))
                if cli.account_status.name != "AVAILABLE": a.cli = None  # kota RPC'si (jSf9Qc) eski çerezle reddedilince kütüphane hesabı UNAUTHENTICATED işaretler: sonraki istek taze Firefox çereziyle bağlansın
                LOG.appendleft({"t": time.strftime("%H:%M:%S"), "hesap": a.ad, "sonuc": "ok", "sn": round(time.time() - t0, 1),
                                "model": model + (" +düşün" if yuksek else ""), "dosya": len(files),
                                "kredi": (k0 - k1) if isinstance(k0, int) and isinstance(k1, int) else None})
                return re.sub(r"\s*\[cite(?::\s*[\d,\s]+)?\]", "", r.text or ""), a.ad
            except ModelHata: raise
            except asyncio.CancelledError:  # diger kol kazandi: hesabi hata saymadan birak
                a.son = time.time(); a.durum = "hazır"; a.cli = None
                kaydet(hesap=a.ad, sonuc="iptal (diger kol kazandi)", kol=kol, sn=round(time.time() - t0, 1), model=model, yuksek=yuksek); raise
            except Exception as e:
                if isinstance(e, ValueError) and "Unknown model" in str(e):  # istek hatası, hesap hatası değil: hesabı dinlendirme
                    a.son = time.time(); a.durum = "hazır"; denenen.add(a.ad)
                    if any(model in x.modeller for x in ACC.values()): continue  # baska hesap tasiyor: orada dene
                    raise BilinmeyenModel(f"bilinmeyen model: {model}")
                if "UNAUTHENTICATED" in str(e) and a.ad not in tazelenen:  # Firefox çerezi döndürmüş: dinlendirmeden taze çerezle bir kez daha dene
                    tazelenen.add(a.ad); a.cli = None; a.durum = "hazır"
                    LOG.appendleft({"t": time.strftime("%H:%M:%S"), "hesap": a.ad, "sonuc": "çerez tazelendi, yeniden deneniyor", "sn": round(time.time() - t0, 1),
                                    "model": model, "dosya": len(files), "kredi": None})
                    continue
                if AG.search(f"{type(e).__name__} {e}"):
                    AG_SON.append((time.time(), a.ad)); son30 = {n for t, n in AG_SON if time.time() - t < 30}
                    if len(son30) >= AG_ESIK:
                        AG_DUR[0] = time.time() + 10; a.son = time.time(); a.durum = "hazır"; a.cli = None
                        kaydet(hesap=a.ad, sonuc=f"ag kesik (bekleniyor): {type(e).__name__}: {str(e)[:80]}", kol=kol, sn=round(time.time() - t0, 1), model=model, yuksek=yuksek, dosya=len(files))
                        LOG.appendleft({"t": time.strftime("%H:%M:%S"), "hesap": a.ad, "sonuc": "ağ kesik, 10 sn bekleniyor", "sn": round(time.time() - t0, 1), "model": model, "dosya": len(files), "kredi": None})
                        continue
                a.hata += 1; a.son = time.time(); ag = bool(AG.search(f"{type(e).__name__} {e}")); gecici = ag or bool(GECICI.search(f"{type(e).__name__} {e}")); zaman = "TimeoutError" in type(e).__name__ or "ReadTimeout" in f"{e}"; a.aralik = min(ARALIK_UST, max(30.0, a.aralik * 2)) if (gecici and not ag and not zaman) else a.aralik; a.kap = 1 if (gecici and "error code" in str(e)) else a.kap; a.seri = 0; a.dinlen = time.time() + (min(SOGUMA_GECICI, 30.0) if ag else 10.0 if zaman else a.aralik if gecici else SOGUMA);
                kaydet(hesap=a.ad, sonuc=f"{type(e).__name__}: {str(e)[:120]}", kol=kol, gecici=gecici, sn=round(time.time() - t0, 1), model=model, yuksek=yuksek, dosya=len(files), uzunluk=len(prompt)); a.son_hata = f"{type(e).__name__}: {str(e)[:160]}"; a.son_hata_t = time.time()
                a.durum = "dinleniyor"; a.cli = None; denenen.add(a.ad)
                LOG.appendleft({"t": time.strftime("%H:%M:%S"), "hesap": a.ad, "sonuc": a.son_hata, "sn": round(time.time() - t0, 1),
                                "model": model, "dosya": len(files), "kredi": None})
    raise RuntimeError("zaman aşımı")


EXT = {"mp3": ".mp3", "wav": ".wav", "m4a": ".m4a", "ogg": ".ogg", "flac": ".flac"}


@app.post("/v1/chat/completions")
async def chat(req: Request):
    b = await req.json(); model = (b.get("model") or VARSAYILAN_MODEL).split("/")[-1]
    if not model.startswith("gemini-"): model = VARSAYILAN_MODEL
    yuksek = str(b.get("reasoning_effort", "")).lower() == "high"
    yukle(); bilinen = {m for a in ACC.values() for m in a.modeller}; bilinen = (bilinen & set(IZINLI)) if IZINLI and bilinen else bilinen
    if bilinen and model not in bilinen:  # hesaba gitmeden reddet (11-16: bilinmeyen ad 10 hesabı dinlenmeye soktu)
        return UJSON({"error": {"message": f"bilinmeyen model: {model}; geçerli: {', '.join(sorted(bilinen))}"}}, status_code=400)
    txt, files, tmp = [], [], tempfile.mkdtemp(prefix="gemweb_")
    for m in b.get("messages", []):
        c = m.get("content")
        parts = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
        for p in parts:
            if p.get("type") == "text": txt.append(p["text"])
            elif p.get("type") == "input_audio":
                f = pathlib.Path(tmp) / f"ses{len(files)}{EXT.get(p['input_audio'].get('format', 'mp3'), '.mp3')}"
                f.write_bytes(base64.b64decode(p["input_audio"]["data"])); files.append(f)
            elif p.get("type") in ("image_url", "video_url", "file"):  # video/ses/pdf: data URL (video_url) ya da OpenAI file parçası
                k = p["type"]; v = p.get(k) or {}
                u = v.get("file_data") or v.get("url") if isinstance(v, dict) else v
                if u.startswith("data:"):
                    head, data = u.split(",", 1); mt = head[5:].split(";")[0]; ext = mimetypes.guess_extension(mt) or "." + mt.split("/")[-1]
                    f = pathlib.Path(tmp) / f"img{len(files)}{ext}"; f.write_bytes(base64.b64decode(data)); files.append(f)
    try: out, ad = await sor("\n\n".join(txt), files, model, yuksek, req)
    except Exception as e: return UJSON({"error": {"message": str(e)}}, status_code=400 if isinstance(e, BilinmeyenModel) else 502 if isinstance(e, ModelHata) else 503)
    finally: shutil.rmtree(tmp, ignore_errors=True)  # 11-16: istek başına gemweb_* klasörü Temp'te kalıyordu (1794 klasör, 2,3 GB)
    return {"id": "gw-" + uuid.uuid4().hex[:12], "object": "chat.completion", "created": int(time.time()), "model": model, "hesap": ad,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": out}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}


@app.get("/v1/models")
async def models():
    ms = sorted({m for a in ACC.values() for m in a.modeller} or {VARSAYILAN_MODEL}); ms = [m for m in ms if not IZINLI or m in IZINLI] or ms
    return {"object": "list", "data": [{"id": m, "object": "model"} for m in ms]}


@app.post("/yenile/{ad}")
async def yenile(ad: str):
    a = ACC.get(ad)
    if not a: return JSONResponse({"error": "yok"}, 404)
    async with a.lock:
        a.cli = None; a.dinlen = 0
        try: await a.client(); a.son_hata = ""
        except Exception as e: a.son_hata = f"{type(e).__name__}: {str(e)[:160]}"; a.durum = "bağlanamadı"
    return {"durum": a.durum}


@app.get("/durum")
async def durum():
    yukle(); now = time.time()
    return {"hesaplar": [{"ad": a.ad, "durum": a.durum if a.dinlen <= now else f"dinleniyor {int(a.dinlen - now)} sn", "ok": a.ok, "hata": a.hata, "aralik": round(a.aralik), "kap": a.kap, "aktif": a.aktif, "kredi_5s": (a.limit.get("current_5h") or {}).get("remaining_credits"),
                          "son": time.strftime("%H:%M:%S", time.localtime(a.son)) if a.son else "-", "son_hata": a.son_hata if (a.dinlen > time.time() or a.durum == "bağlanamadı" or time.time() - getattr(a, "son_hata_t", 0) < 600) else "",
                          "limit": a.limit, "modeller": a.modeller, "kaynak": (f"firefox /u/{a.d.get('u', 0)}" if "firefox" in a.d else "çerez") + (" · proxy" if a.d.get("proxy") else ""), "eposta": a.d.get("eposta", "")} for a in ACC.values()],
            "log": list(LOG), "aralik": ARALIK, "soguma": SOGUMA, "varsayilan": VARSAYILAN_MODEL}


@app.get("/", response_class=HTMLResponse)
async def panel(): return (W / "panel.html").read_text(encoding="utf-8")


@app.on_event("startup")
async def basla():
    yukle()
    async def bagla(a):
        try: await a.client()
        except Exception as e: a.son_hata = f"{type(e).__name__}: {str(e)[:160]}"; a.durum = "bağlanamadı"
    for a in ACC.values(): await asyncio.create_task(bagla(a))


if __name__ == "__main__":
    import uvicorn; uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("GEMWEB_PORT", 8790)), log_level="warning")
