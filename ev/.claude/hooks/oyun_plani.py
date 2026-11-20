"""Oyun plani kancasi (kullanici 11-19: "oyun planini kursun, gerekiyorsa hemen alt ajan acsin; sabit sayi yok").
UserPromptSubmit: is mesajinda (uzun istem) 1 satir: once oyun plani, bagimsiz parcalar AYNI mesajda paralel ajana.
PostToolUse (ana oturum): Agent acmadan ardisik ESIK okuma/kabuk cagrisinda 1 satir hatirlatma; istem basina en fazla 2.
Engellemez, model harcamaz. Kayit: state/oyun_log.jsonl (26 Kas olcumu icin).
"""
import json, os, sys, time

ST = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "state")
ESIK, MAX_ISTEM, MIN_ISTEM = 5, 3, 80
OKUMA = {"Read", "Grep", "Glob", "Bash", "PowerShell", "WebFetch", "WebSearch"}
PLAN = ("[oyun plani] Is birden fazla adimliysa ilk araç mesajindan once oyun planini kur: birbirini beklemeyen parcalari ayir, "
        "her birine alt ajani AYNI mesajda paralel ac (sayi ise gore, sabit yok; sinir paylasilan kaynak: okuma/arastirma 8-10, "
        "gemweb/G-Labs/GPU/render 4, ayni dosyaya iki yazan yok). Model+effort Agent cagrisinda ACIK (kullanici 11-19): ONCE haiku; "
        "yetersiz kalirsa ya effort artir ya sonnet'e gec (ise gore sen karar ver); alt ajan YALNIZ haiku ya da sonnet; OPUS ALT AJAN ACMA (Opus danisman yok); token ve isi bitirme acisindan hangisi mantikliysa o. "
        "Her ajana butce ver: ~25 arac turu, buyuk dosyayi parca/grep ile oku, rapor <=40 satir. "
        "TOKEN: her ayri arac mesaji tum baglami (~130k) yeniden okutur; bagimsiz okuma/komutlari TEK mesajda paralel cagir "
        "ya da tek Bash'te birlestir (11-19 olcum: ana Opus cagrilarinin %45'i ust uste tek okuma adimiydi). Sen bagimli/sirali kismi ve karari yap. Tek adimlik isse gec.")
DURT = ("[oyun plani] Ajan acmadan {n} ardisik okuma/kabuk cagrisi yaptin; her biri tum baglami yeniden okutuyor. "
        "Siradaki okumalar birbirini beklemiyorsa TEK mesajda paralel cagir ya da tek komutta birlestir; uzun kesifse Haiku ajana ver. "
        "Sonuca gore adim adim gitmen gerekiyorsa devam et.")


def main():
    d = json.load(sys.stdin)
    if d.get("agent_id"):
        return  # alt ajanlar kendi isini yapar
    os.makedirs(ST, exist_ok=True)
    sid = d.get("session_id") or "x"
    sp = os.path.join(ST, f"oyun_{sid}.json")
    try:
        s = json.load(open(sp, encoding="utf-8"))
    except (OSError, ValueError):
        s = {"seri": 0, "durt": 0}
    olay = d.get("hook_event_name", "")
    cikti, kayit = None, None
    if olay == "UserPromptSubmit":
        s = {"seri": 0, "durt": 0}
        p = str(d.get("prompt", ""))
        if len(p) >= MIN_ISTEM and not p.lstrip().startswith(("<", "/")):
            cikti, kayit = PLAN, "plan"
    elif olay == "PostToolUse":
        ad = d.get("tool_name", "")
        if ad in ("Agent", "Task"):
            t = d.get("tool_input") or {}
            kayit = f"ajan:{t.get('subagent_type') or 'gp'}:{t.get('model') or '-'}"
            s["seri"] = 0
        elif ad in OKUMA:
            s["seri"] += 1
            if s["seri"] >= ESIK and s["durt"] < MAX_ISTEM:
                cikti, kayit = DURT.format(n=s["seri"]), "durt"
                s["durt"] += 1
                s["seri"] = 0
    tmp = f"{sp}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f)
    os.replace(tmp, sp)
    if kayit:
        with open(os.path.join(ST, "oyun_log.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.strftime("%m-%d %H:%M"), "sid": sid[:8], "olay": kayit}) + "\n")
    if cikti:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": olay, "additionalContext": cikti}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
