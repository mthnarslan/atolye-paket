"""Kullanim: python asr.py ses.mp3 --json cikti.json --model small --dil tr
Kullanim: transcribe(yol, model='small', dil=None, kelime=False)
Ses ffmpeg ile 16 kHz mono float32 olarak okunur.
CUDA DLL dizinleri otomatik eklenir; CUDA hatasinda CPU int8 kullanilir.
"""
import argparse, ctypes, json, os, subprocess, sys
from pathlib import Path

def _dll_dirs():
    root = Path(sys.prefix) / 'Lib' / 'site-packages' / 'nvidia'
    dirs = []
    if root.exists():
        dirs = [str(p / 'bin') for p in root.iterdir() if (p / 'bin').exists()]
        for d in dirs:
            os.add_dll_directory(d)
        # ctranslate2 cublas'i sonradan LoadLibrary ile yukler; PATH olmadan add_dll_directory yetmiyor
        os.environ['PATH'] = os.pathsep.join(dirs + [os.environ.get('PATH', '')])
    return dirs

def _audio(path):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', '1', '-ar', '16000', 'pipe:1'], stdout=subprocess.PIPE, check=True)
    import numpy as np
    return np.frombuffer(p.stdout, dtype=np.float32)

def transcribe(yol, model='small', dil=None, kelime=False):
    audio = _audio(yol)
    _dll_dirs()
    from faster_whisper import WhisperModel
    device, compute = 'cuda', 'float16'
    try:
        wm = WhisperModel(model, device=device, compute_type=compute)
        used = 'cuda'
    except Exception as exc:
        if not any(x in str(exc).lower() for x in ('cuda', 'cublas', 'cudnn', 'out of memory', 'dll')):
            raise
        wm = WhisperModel(model, device='cpu', compute_type='int8')
        used = 'cpu'
    try:
        segs, _ = wm.transcribe(audio, language=dil, word_timestamps=kelime)
        list_segs = list(segs)
    except Exception as exc:
        if used != 'cuda' or not any(x in str(exc).lower() for x in ('cuda', 'cublas', 'cudnn', 'out of memory', 'dll')):
            raise
        print(f'asr: CUDA hatasi, CPU int8: {exc}', file=sys.stderr)
        wm = WhisperModel(model, device='cpu', compute_type='int8')
        used = 'cpu'
        list_segs = list(wm.transcribe(audio, language=dil, word_timestamps=kelime)[0])
    out = []
    for s in list_segs:
        row = {'start': s.start, 'end': s.end, 'text': s.text}
        if kelime:
            row['words'] = [{'start': w.start, 'end': w.end, 'word': w.word, 'probability': w.probability} for w in (s.words or [])]
        out.append(row)
    return out, used

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('ses'); ap.add_argument('--json', dest='output'); ap.add_argument('--model', default='small'); ap.add_argument('--dil'); ap.add_argument('--kelime', action='store_true')
    a = ap.parse_args(); result, device = transcribe(a.ses, a.model, a.dil, a.kelime)
    payload = {'device': device, 'segments': result}
    if a.output: Path(a.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    else: print(json.dumps(payload, ensure_ascii=False))
