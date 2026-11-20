"""Atölye paketi kurucusu (arkadaşın bilgisayarında koşar).

  python kur.py              -> ev/ altındaki her şeyi kullanıcı klasörüne kopyalar, C:\\Users\\meteh yollarını senin klasörüne çevirir
  python kur.py --kuru       -> hiçbir şey yazmadan ne yapacağını söyler
  python kur.py --hedef D:/x -> deneme için başka bir klasöre kurar

Güncelleme: `git pull` sonra yine `python kur.py`. Senin elle değiştirdiğin dosyalar EZİLMEZ (son kurulumdaki
özetle karşılaştırılır); onlar "çakışma" diye listelenir, Claude'un birleştirir.
Hesap, çerez, anahtar, ses referansı bu pakette YOK; her makine kendi hesaplarını kurar.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

PAKET = Path(__file__).resolve().parent
KAYNAK = PAKET / 'ev'
ESKI = 'C:/Users/meteh'
METIN = {'.py', '.md', '.json', '.txt', '.ps1', '.sh', '.mjs', '.js', '.html', '.css', '.toml', '.cfg', '.ini', '.yaml', '.yml', '.bat'}
ORTAM = {  # kullanıcı ortam değişkenleri (yoksa yazılır, varsa dokunulmaz)
    'DOCUMENTARY_VOICE_ENGINE': 'pocket',
    'DOCUMENTARY_YT_COOKIES_BROWSER': 'firefox',
    'DOCUMENTARY_PINPOINT': '0',
    'DOCUMENTARY_FLASH_BACKEND': 'gemweb',
    'DOCUMENTARY_SEARXNG': 'http://127.0.0.1:8888',
    'PYTHONIOENCODING': 'utf-8',
}


def cevir(t: str, ev: Path) -> str:
    fw = ev.as_posix()                      # C:/Users/ali
    bs = str(ev).replace('/', '\\')         # C:\Users\ali
    t = re.sub(r'C:\\\\Users\\\\meteh', bs.replace('\\', '\\\\\\\\'), t, flags=re.I)  # "C:\\Users\\meteh" (py dizgesi)
    t = re.sub(r'C:\\Users\\meteh', bs.replace('\\', '\\\\'), t, flags=re.I)
    t = re.sub(r'C:/Users/meteh', fw, t, flags=re.I)
    t = re.sub(r'/c/Users/meteh', '/' + fw[0].lower() + fw[2:], t, flags=re.I)
    return t


def ozet(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kuru', action='store_true')
    ap.add_argument('--hedef', default=str(Path.home()))
    a = ap.parse_args()
    ev = Path(a.hedef)
    durum_yol = ev / '.atolye_kur_durum.json'
    durum = json.loads(durum_yol.read_text(encoding='utf-8')) if durum_yol.exists() else {}
    yeni, guncel, ayni, cakisma = 0, 0, 0, []
    for f in sorted(KAYNAK.rglob('*')):
        if not f.is_file():
            continue
        rel = f.relative_to(KAYNAK).as_posix()
        if rel == '.claude/settings_hooks.json':
            continue
        veri = f.read_bytes()
        if f.suffix.lower() in METIN:
            veri = cevir(veri.decode('utf-8', errors='ignore'), ev).encode('utf-8')
        h = ev / rel
        if h.exists():
            mevcut = h.read_bytes()
            if mevcut == veri:
                ayni += 1; durum[rel] = ozet(veri); continue
            if durum.get(rel) != ozet(mevcut):   # elle değiştirilmiş ya da paketten gelmemiş
                cakisma.append(rel); continue
            guncel += 1
        else:
            yeni += 1
        if not a.kuru:
            h.parent.mkdir(parents=True, exist_ok=True)
            h.write_bytes(veri)
            durum[rel] = ozet(veri)
    # hook'lar: ~/.claude/settings.json içine birleştir (yedekle)
    hk = json.loads(cevir((KAYNAK / '.claude/settings_hooks.json').read_text(encoding='utf-8'), ev))
    sy = ev / '.claude/settings.json'
    s = json.loads(sy.read_text(encoding='utf-8')) if sy.exists() else {}
    if s.get('hooks') != hk['hooks'] and not a.kuru:
        if sy.exists():
            shutil.copy2(sy, sy.with_suffix('.json.kur_yedek'))
        s['hooks'] = hk['hooks']
        sy.parent.mkdir(parents=True, exist_ok=True)
        sy.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding='utf-8')
    # çalışma klasörleri
    for d in ['Kanallar/bekci_log', 'CodexOutputs', 'Belgesel_Teslim/_slots', 'Belgesel_Teslim/teslim', 'voices']:
        if not a.kuru:
            (ev / d).mkdir(parents=True, exist_ok=True)
    ortam = dict(ORTAM, DOCUMENTARY_DELIVERY_ROOT=str(ev / 'Belgesel_Teslim' / 'teslim'),
                 DOCUMENTARY_SLOT_DIR=str(ev / 'Belgesel_Teslim' / '_slots'))
    yazilan = []
    if a.hedef == str(Path.home()) and os.name == 'nt':
        for k, v in ortam.items():
            if os.environ.get(k) is None:
                yazilan.append(k)
                if not a.kuru:
                    subprocess.run(['setx', k, v], capture_output=True)
    if not a.kuru:
        durum_yol.write_text(json.dumps(durum, indent=0), encoding='utf-8')
    print(f"{'[KURU] ' if a.kuru else ''}yeni {yeni}, güncellenen {guncel}, aynı {ayni}, çakışma {len(cakisma)}")
    for c in cakisma[:40]:
        print('  ÇAKIŞMA (senin değiştirdiğin, ezilmedi):', c)
    if yazilan:
        print('ortam değişkeni yazıldı (yeni terminalde geçerli):', ', '.join(yazilan))
    print('Sıradaki adım: KURULUM_REHBERI.md -> "3. Servisler"')


if __name__ == '__main__':
    main()
