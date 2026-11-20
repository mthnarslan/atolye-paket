"""gpt_isci: Claude komutan, is GPT/Flash iscisine (codex exec). Claude limiti yemez; Claude sadece SONUC.md'yi kontrol eder.
Sira: GPT 9router cx/gpt-6.2-sol (VDS :20128) -> GPT VDS OceanAPI :8765 (sinirsiz, 'oc') -> limit/hata olursa GPT ChatGPT aboneligi -> Flash (9router) -> o da dolarsa CLAUDE_GEREK (Claude alt ajani kullan).
  python gpt_isci.py tek --ad S1 --klasor D --gorev "..." [--gorev-dosya f.md] [--model sol|astra|luna|flash] [--effort low|medium|high] [--sure-dk 40]
  python gpt_isci.py toplu gorevler.json [--paralel 8] [--agir]      # json: [{"ad","klasor","gorev"|"gorev_dosya","model"?,"effort"?}]
Model: sol = adim adim uygulama (varsayilan), astra = emin olunmayan/ikinci gorus, luna = buyuk veri temizleme/sayma, flash = yedek.
Paralel: varsayilan 8; --agir (film/render/model yukleyen test) 4; Flash en fazla 2 (9router kota/ban riski).
Cikti: isci basina tek satir 'AD model sure STATUS yol'; cikis 0 = hepsi PASS. 'PASS' isci beyanidir: Claude kanit/ dosyalarini kontrol etmeden kabul etmez."""
import argparse, json, os, re, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
MODELLER = {'sol': 'gpt-6.1-sol', 'astra': 'gpt-6-astra', 'luna': 'gpt-6-luna', 'flash': 'ag/gemini-3.8-flash-high'}
NINE = {'sol': 'cx/gpt-6.2-sol', 'astra': 'cx/gpt-6-astra', 'luna': 'cx/gpt-6-luna'}  # VDS 9router ChatGPT (11-20: 6.2-sol codex 8 gercek gorevde 12/16; GPT_ISCI_9R=0 kapatir)
OC_YOK = {'luna': 'sol'}  # VDS OceanAPI'de gpt-6-luna yok (400 'Model not found', 11-18) -> VDS'te sol kosar
FLASH_SAGLAYICI = ['-c', 'model_provider="ninerouter"', '-c',
    'model_providers.ninerouter={name="9router",base_url="http://100.104.78.117:20128/v1",env_key="NINEROUTER_API_KEY",wire_api="responses"}']
OCEAN_SAGLAYICI = ['-c', 'model_provider="ocean"', '-c',
    'model_providers.ocean={name="OceanAPI",base_url="http://100.104.78.117:8765/v1",env_key="OCEANAPI_API_KEY",wire_api="responses"}']
LIMIT = re.compile(r'usage limit|rate.?limit|quota|429|too many requests|insufficient|exceeded', re.I)
flash_kilit = threading.Semaphore(2)
KURAL = """Sen bir isci ajansin; komutan Claude. Gorevi adim adim, eksiksiz uygula; yorum katma, kapsami genisletme.
Klasorun: {k}. Butun calisma dosyalarin, loglarin ve sonucun burada.
Kesin kurallar:
1. Her sayi (sure, adet, oran, boyut) bir komutun ham ciktisindan gelir. O ciktiyi {k}/kanit/ altina UTF-8 metin dosyasi olarak kaydet (PowerShell'de Out-File -Encoding utf8); sayiyi mumkunse iki farkli yolla dogrula; SONUC.md'de sayinin yanina dosya adini yaz. Elle yazilmis, tahmini ya da kopyalanmis sayi = gorev basarisiz.
2. Prod koduna sadece gorev acikca istiyorsa dokun; tercihen degisikligi {k}/yama.diff olarak yaz. git commit, push, dosya/klasor silme YOK.
3. QA esikleri, hakem istemleri, testler, yt_gate, NVENC/slot sinirlari gevsetilmez. Baslatmadigin sureci oldurme. Toplu video taramasi yok.
4. Gercek test gecene kadar calis; ayni varsayimla iki deneme tutmadiysa dur ve nedenini yaz.
5. Sonunda {k}/SONUC.md yaz (Turkce, en fazla 15 satir): ne yaptin, olculen sonuc + kanit dosyasi, kalan is. SON SATIR tam olarak 'STATUS: PASS' ya da 'STATUS: FAIL <neden>' olmali.
{onceki}
GOREV:
{g}"""

def isci(ad, klasor, gorev, model='sol', effort='low', sure_dk=40):
    k = os.path.abspath(klasor); os.makedirs(os.path.join(k, 'kanit'), exist_ok=True)
    son = os.path.join(k, 'SONUC.md')
    onceki = f'Onceki deneme var: {son} ve {k}/NOT.md (varsa) oku, kaldigi yerden devam et, NOT.md onu ezer.' if os.path.exists(son) else ''
    p = KURAL.format(k=k, g=gorev, onceki=onceki)
    sira = (([('9r', model)] if os.environ.get('GPT_ISCI_9R', '1') != '0' else []) + [('oc', OC_YOK.get(model, model)), ('gpt', model)] if model != 'flash' else []) + [('flash', 'flash')]
    for yol, m in sira:
        t0 = time.time(); log = os.path.join(k, f'codex_{m}_{yol}.log' if yol != 'flash' else 'codex_flash.log')
        cmd = [shutil.which('codex') or 'codex', 'exec', '--skip-git-repo-check', '-s', 'danger-full-access', '-C', k, '-m', NINE[m] if yol == '9r' else MODELLER[m], '-c', f'model_reasoning_effort="{effort}"',
               '--output-last-message', os.path.join(k, 'son_mesaj.txt')] + {'flash': FLASH_SAGLAYICI, '9r': FLASH_SAGLAYICI, 'oc': OCEAN_SAGLAYICI}.get(yol, []) + [p]
        kilit = flash_kilit if m == 'flash' else None
        if kilit: kilit.acquire()
        try:
            with open(log, 'w', encoding='utf-8', errors='replace') as lf:
                pr = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=lf, stderr=subprocess.STDOUT, cwd=k)
                try: pr.wait(timeout=sure_dk * 60); rc = pr.returncode
                except subprocess.TimeoutExpired:
                    subprocess.run(['taskkill', '/T', '/F', '/PID', str(pr.pid)], capture_output=True) if os.name == 'nt' else pr.kill()
                    rc = 'sure'
        finally:
            if kilit: kilit.release()
        dk = (time.time() - t0) / 60
        durum = 'FAIL sonuc-yok'
        if os.path.exists(son) and os.path.getmtime(son) >= t0:
            sat = [s.strip() for s in open(son, encoding='utf-8', errors='replace') if s.strip()]
            if sat and re.match(r'STATUS: (PASS|FAIL)', sat[-1]): durum = sat[-1][8:]
        if rc == 'sure': durum = f'FAIL sure-doldu {sure_dk}dk'
        kuyruk = open(log, encoding='utf-8', errors='replace').read()[-4000:]
        if durum.startswith('FAIL sonuc-yok') and (LIMIT.search(kuyruk) or (yol in ('oc', '9r') and rc not in (0, 'sure'))) and (yol, m) != sira[-1]:
            continue  # limit doldu / VDS hatasi -> siradaki yol
        if durum.startswith('FAIL sonuc-yok') and LIMIT.search(kuyruk): durum = 'CLAUDE_GEREK (GPT ve Flash limitte)'
        return f'{ad:20s} {m:5s}/{yol:5s} {dk:5.1f}dk {durum[:90]}  {son}'
    return f'{ad:20s} -     -      CLAUDE_GEREK  {son}'

def main():
    a = argparse.ArgumentParser(); s = a.add_subparsers(dest='k', required=True)
    t = s.add_parser('tek'); t.add_argument('--ad', required=True); t.add_argument('--klasor', required=True)
    t.add_argument('--gorev', default=''); t.add_argument('--gorev-dosya'); t.add_argument('--model', default='sol', choices=MODELLER)
    t.add_argument('--effort', default='low'); t.add_argument('--sure-dk', type=float, default=40)
    b = s.add_parser('toplu'); b.add_argument('dosya'); b.add_argument('--paralel', type=int, default=8); b.add_argument('--agir', action='store_true')
    b.add_argument('--sure-dk', type=float, default=40)
    x = a.parse_args()
    oku = lambda d: d.get('gorev') or open(d['gorev_dosya'], encoding='utf-8').read()
    if x.k == 'tek':
        r = isci(x.ad, x.klasor, oku({'gorev': x.gorev, 'gorev_dosya': x.gorev_dosya}), x.model, x.effort, x.sure_dk); print(r, flush=True)
        sys.exit(0 if ' PASS' in r else 1)
    isler = json.load(open(x.dosya, encoding='utf-8'))
    n = min(x.paralel, 4 if x.agir else 8)
    with ThreadPoolExecutor(n) as ex:
        sonuc = list(ex.map(lambda d: isci(d['ad'], d['klasor'], oku(d), d.get('model', 'sol'), d.get('effort', 'low'), d.get('sure_dk', x.sure_dk)), isler))
    for r in sonuc: print(r)
    sys.exit(0 if all(' PASS' in r for r in sonuc) else 1)
if __name__ == '__main__': main()
