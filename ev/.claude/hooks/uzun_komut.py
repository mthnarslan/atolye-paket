"""PreToolUse(Bash): ~7,5 KB ustu komutu calismadan durdurur.
Olcum 11-18 (tum dokumler, 6951 heredoc'lu komut): <=7 KB 6809'da 1 hata; 8 KB ustu %90-100 'unexpected EOF'
(Windows komut satiri siniri komutu kesiyor). 7500 bayt esigi 113 hatanin 109'unu yakalar, 6838 basaridan 16'sina dokunur.
Ders: beyin/ders/bash-uzun-komut-8kb-1118. Olcum betigi: Kanallar/ortak_duzelt/heredoc_boy.py
"""
import json, re, sys

ESIK = 7500
# >=60 sn sabit uyku: sleep 60, Start-Sleep 90, time.sleep(178). Kisa uykular (sleep 5) serbest.
UYKU = re.compile(r"(?:\bsleep\s+|Start-Sleep\s+(?:-Seconds\s+)?|time\.sleep\(\s*)([6-9]\d|\d{3,})(?:\.\d+)?\b")


def main():
    d = json.load(sys.stdin)
    if d.get("tool_name") not in ("Bash", "PowerShell"):
        return
    ti = d.get("tool_input") or {}
    cmd = str(ti.get("command", ""))
    n = len(cmd.encode("utf-8"))
    sys.stdout.reconfigure(encoding="utf-8")
    m = UYKU.search(cmd)
    if m and not ti.get("run_in_background") and "bekci.py" not in cmd:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Sabit uyku ile yoklama ({m.group(0).strip()[:40]}): 11-18 olcumu 21 gunde ~24 saat bu tur beklemeye gitti. "
                "Bunun yerine `python C:/Users/meteh/Kanallar/bekci.py --ad X --log <log> --pid <pid>` (ya da `bekci.py --ad X -- komut`) "
                "kullan: bitis/hata/takilmada hemen doner. Ana oturumda run_in_background ile.")}}, ensure_ascii=False))
        return
    if d.get("tool_name") != "Bash" or n <= ESIK:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"Bash komutu {n} bayt: Windows'ta ~7,5 KB ustu komut kesilip 'unexpected EOF' ile bozuluyor "
            "(11-18 olcumu: 8 KB ustu %90-100 hata). Dosya icerigini Write araciyla yaz, sonra kisa bir komutla calistir; "
            "uzun betigi parcalara bolme, dosyaya yaz.")}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
