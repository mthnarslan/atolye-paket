"""Tuzak hook'u: bilinen tekrar eden hatada / ortak araca ilk dokunusta Claude'a 1-2 satir not duser. Engellemez, model harcamaz.
Olaylar: PreToolUse (olay=komut kurallari), PostToolUse + PostToolUseFailure (olay=cikti kurallari + bekcisiz arka plan hatirlatmasi).
Kurallar: C:/Users/meteh/beyin/tuzak.json. Ayni oturum+ajan+kural+surum bir kez; sikistirmada sifirlanir (--sifirla, SessionStart compact).
Atesleme kaydi: state/tuzak_log.jsonl (not gosterildi mi, sonra yine oldu mu -> araca gomulmeye aday). Konsey 11-16: Fable + astra.
"""
import glob, json, os, re, sys, time

KURAL = r"C:\Users\meteh\beyin\tuzak.json"
ST = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "state")
MAX_NOT, MAX_OTURUM = 300, 5
HARITA = r"C:\Users\meteh\Kanallar\venv_haritasi.json"


def yaz_json(p, v):
    tmp = f"{p}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False)
    os.replace(tmp, p)


def metin(x):
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        return " ".join(metin(v) for v in x.values())
    if isinstance(x, list):
        return " ".join(metin(v) for v in x)
    return ""


def main():
    d = json.load(sys.stdin)
    os.makedirs(ST, exist_ok=True)
    sid = d.get("session_id") or "x"
    if "--sifirla" in sys.argv:
        for p in glob.glob(os.path.join(ST, f"tuzak_{sid}_*.json")):
            os.remove(p)
        return
    olay = d.get("hook_event_name", "")
    t = d.get("tool_input") or {}
    cmd = str(t.get("command", ""))
    notlar = []

    if olay == "PreToolUse":
        tur, hedef = "komut", cmd
    else:
        tur, hedef = "cikti", metin(d.get("tool_response")) + " " + str(d.get("error", ""))
        mm = re.search(r"No module named ['\"]([a-zA-Z0-9_.]+)", hedef)
        if mm:
            mod = mm.group(1).lower()
            try:
                hm = json.load(open(HARITA, encoding="utf-8"))
                yollar = hm.get(mod, [])
                n = (mod + " su python'da kurulu: " + ", ".join(yollar)) if yollar else (mod + " hicbir python'da kurulu degil")
                notlar.append(("venv_harita:" + mod, n[:MAX_NOT]))
            except (OSError, ValueError):
                pass
        if re.search(r"beyin[\\/]|tuzak|\.jsonl|ara\.py|tekrar\.py", cmd):  # ders/kayit okurken hata metni gecer: yanlis tetik
            hedef = ""
        if t.get("run_in_background") and "bekci" not in cmd.lower():  # eski bekci_hatirlat.py
            notlar.append(("bekci", "Bu arka plan isi bekcisiz basladi. 2 dk'dan uzun surecekse simdi bekci kur: "
                           "python C:/Users/meteh/Kanallar/bekci.py --ad <ad> --log <log> --pid <pid> (run_in_background). "
                           "Kisa is ya da surekli sunucuysa gerek yok."))

    try:
        kurallar = json.load(open(KURAL, encoding="utf-8")).get("kurallar", [])[:30]
    except (OSError, ValueError):
        kurallar = []
    sp = os.path.join(ST, f"tuzak_{sid}_{d.get('agent_id') or 'ana'}.json")
    try:
        gorulen = json.load(open(sp, encoding="utf-8"))
    except (OSError, ValueError):
        gorulen = {}
    log = []
    for k in kurallar:
        if k.get("olay") != tur:
            continue
        try:
            if not re.search(k["kalip"], hedef):
                continue
        except (re.error, KeyError):
            continue
        anahtar = f"{k['id']}@{k.get('surum', 1)}"
        log.append({"t": time.strftime("%m-%d %H:%M"), "sid": sid[:8], "kural": anahtar,
                    "gosterildi": anahtar not in gorulen})
        if anahtar in gorulen or len(gorulen) >= MAX_OTURUM:
            continue
        gorulen[anahtar] = time.time()
        n = k.get("not", "")[:MAX_NOT]
        if k.get("ders"):
            n += f" (beyin/ders/{k['ders']})"
        notlar.append((k["id"], n))
    if log:
        with open(os.path.join(ST, "tuzak_log.jsonl"), "a", encoding="utf-8") as f:
            f.write("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in log))
    if not notlar:
        return
    yaz_json(sp, gorulen)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": olay,
          "additionalContext": "[tuzak] " + " | ".join(n for _, n in notlar)}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
