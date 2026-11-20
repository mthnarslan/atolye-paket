"""Ortak gemweb istemcisi (:8790). Kanallar kendi ayristiricisini yazmasin, bunu kullansin (konsey 11-16).
    import sys; sys.path.insert(0, r"C:/Users/meteh/Kanallar"); import gemweb
    txt = gemweb.sor("soru", gorseller=["a.png"])            # metin; ret/cop/hata -> yeniden dener, sonunda GemwebHata
    obj = gemweb.sor_json("JSON dondur ...", gorseller=[...]) # ```json citini soyar, parse eder, olmazsa yeniden dener
    gemweb.json_al(metin)                                     # yalniz ayristirma (cit/bos metin -> None)
Ogrenilenler (beyin/ders/gemweb-*-1116): hydrogen + low varsayilan; yanit ```json citli gelir; HTTP 200 ile
"Sorry I can't help with that image" = ret (ret alinca grubu tek tek bol: GemwebRet); "_965" gibi cop = yeniden dene;
502 = model isi yapamadi. Tum makinede ayni anda en fazla SLOT (30) istek (sira sunucuda FIFO): dosya kilidiyle oturumlar arasi paylasilir.
"""
import base64, json, mimetypes, os, re, time
import msvcrt
import requests

URL = "http://127.0.0.1:8790/v1/chat/completions"
SLOT = int(os.environ.get("GEMWEB_SLOT", "30"))  # 11-19: 10 slot 0,5 sn yoklamayla adil degildi (bekleyen 345 sn kaldi); sirayi sunucu FIFO tutar, bu yalniz kacak korumasi
KILIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gemweb_slot")
RET = re.compile(r"can.?t help with (that|this) image|unable to help with (that|this) image|bu görselle ilgili yardımcı olamam", re.I)


class GemwebHata(RuntimeError): pass
class GemwebRet(GemwebHata): pass  # model gorseli reddetti: grubu tek tek bol


class _Slot:
    """Makine geneli sayac: SLOT kilit dosyasindan bos olani tutar."""
    def __enter__(self):
        os.makedirs(KILIT_DIR, exist_ok=True)
        while True:
            for i in reversed(range(SLOT)):  # yeni surecler ustten alir: eski SLOT=10 surecler 0-9'u bos bulur
                f = open(os.path.join(KILIT_DIR, f"{i}.lock"), "a+b")
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1); self.f = f; return self
                except OSError:
                    f.close()
            time.sleep(0.5)

    def __exit__(self, *a):
        try:
            msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.f.close()


def json_al(metin):
    """```json citini ve etrafindaki yaziyi soyup ilk JSON nesne/dizisini dondurur; yoksa None."""
    if not metin:
        return None
    m = re.search(r"```(?:json)?\s*(.*?)```", metin, re.S)
    s = (m.group(1) if m else metin).strip()
    for aday in (s, s[min([i for i in (s.find("{"), s.find("[")) if i >= 0] or [0]):]):
        try:
            return json.loads(aday)
        except ValueError:
            pass
    try:
        return json.JSONDecoder().raw_decode(s[min([i for i in (s.find("{"), s.find("[")) if i >= 0] or [0]):])[0]
    except ValueError:
        return None


def _parca(yol):
    tip = mimetypes.guess_type(yol)[0] or "image/png"
    b64 = base64.b64encode(open(yol, "rb").read()).decode()
    if tip.startswith("audio/"):
        return {"type": "input_audio", "input_audio": {"data": b64, "format": tip.split("/")[1].replace("mpeg", "mp3")}}
    return {"type": "image_url", "image_url": {"url": f"data:{tip};base64,{b64}"}}


_MODELLER = []


def _model_kontrol(model):
    # 11-16: bilinmeyen ad (gemini-4-argon) sunucuda 10 hesabin hepsini 15 dk dinlenmeye soktu -> gondermeden once kontrol
    if not _MODELLER:
        try:
            _MODELLER.extend(m["id"] for m in requests.get(URL.replace("chat/completions", "models"), timeout=10).json()["data"])
        except Exception:
            return
    if model not in _MODELLER:
        raise ValueError(f"gemweb'de '{model}' yok; var olanlar: {_MODELLER}")


def _istek(istem, gorseller, effort, model, zaman):
    _model_kontrol(model)
    icerik = [{"type": "text", "text": istem}] + [_parca(g) for g in gorseller or []]
    with _Slot():
        r = requests.post(URL, json={"model": model, "reasoning_effort": effort,
                                     "messages": [{"role": "user", "content": icerik}]}, timeout=zaman)
    if r.status_code == 502:
        raise GemwebHata(f"502 model isi yapamadi: {r.text[:160]}")
    r.raise_for_status()
    return (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "") or ""


def _sunucu_bekle(sure=300):
    """Sunucu ayaga kalkana kadar bekler (yeniden baslatma ~40 sn). Geldiyse True."""
    son = time.time() + sure
    while time.time() < son:
        try:
            if requests.get(URL.replace("chat/completions", "models"), timeout=5).ok: return True
        except requests.RequestException:
            pass
        time.sleep(3)
    return False


def sor(istem, gorseller=None, effort="low", model="gemini-4-hydrogen", deneme=3, zaman=400, en_az=2):  # 11-19: 1095 ~95 sn sonra gelir, sunucu baska hesapta dener; 200 sn yetmiyordu
    """Metin yanit. Ret -> GemwebRet (tekrar denemez). Bos/cop (<en_az karakter ya da '_123') -> yeniden dener."""
    son = None; kopma = 0; i = 0
    while i < deneme:
        try:
            t = _istek(istem, gorseller, effort, model, zaman)
        except requests.ConnectionError as e:  # 11-19: sunucu yeniden basliyor (~40 sn); eskiden 3 deneme 9 sn'de biter, film adimi duserdi
            son = e; kopma += 1
            if kopma <= 3 and _sunucu_bekle(): continue  # deneme sayilmaz
            i += 1; continue
        except (requests.RequestException, GemwebHata) as e:
            i += 1
            son = e; time.sleep((30 if getattr(getattr(e, "response", None), "status_code", 0) == 503 else 3) * i); continue  # 503 = tum hesaplar dinlenmede
        if RET.search(t):
            raise GemwebRet(t[:160])
        if len(t.strip()) < en_az or re.fullmatch(r"_?\d{1,4}", t.strip()):
            son = GemwebHata(f"cop yanit: {t[:40]!r}"); i += 1; continue
        return t
    raise GemwebHata(f"{deneme} denemede olmadi: {son}")


def sor_json(istem, gorseller=None, deneme=3, **kw):
    """JSON yanit; parse olmazsa yeniden sorar."""
    son = ""
    for _ in range(deneme):
        son = sor(istem, gorseller, deneme=deneme, **kw)
        v = json_al(son)
        if v is not None:
            return v
    raise GemwebHata(f"JSON cikmadi: {son[:120]!r}")


if __name__ == "__main__":
    print(sor_json('Return only JSON: {"ok": true, "n": 7}'))
