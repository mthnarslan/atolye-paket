"""gemini_webapi'ye çoklu Google oturumu (/u/N/) desteği: Endpoint'i görev başına (contextvar) hesap indeksine göre çevirir.
Kullanım: import authuser; authuser.kur(); sonra her hesabın işini `authuser.AU.set(n)` ile ayarlanmış bağlamda çalıştır."""
import contextvars, importlib
from gemini_webapi.constants import Endpoint as _E

AU = contextvars.ContextVar("authuser", default=0)
_GEM = ("INIT", "GENERATE", "BATCH_EXEC")


class _Proxy:
    def __getattr__(self, k):
        v = str(getattr(_E, k)); n = AU.get()
        if n and k in _GEM: v = v.replace("https://gemini.google.com/", f"https://gemini.google.com/u/{n}/", 1)
        return v


def kur():
    p = _Proxy()
    for mod in ("gemini_webapi.client", "gemini_webapi.utils.get_access_token", "gemini_webapi.utils.upload_file", "gemini_webapi.utils.rotate_1psidts"):
        m = importlib.import_module(mod)
        if hasattr(m, "Endpoint"): m.Endpoint = p
