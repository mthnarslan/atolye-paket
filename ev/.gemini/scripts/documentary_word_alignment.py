"""Align approved synthesis text to actual master audio with installed Whisper attention."""
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

from documentary_voice_engine import file_hash, load_json, save_json

VERSION = 'approved-word-alignment-v1'


def align_words(out):
    from faster_whisper import WhisperModel
    from faster_whisper.tokenizer import Tokenizer
    out = Path(out)
    manifest = load_json(out/'voice_manifest.json')
    language = manifest.get('language', 'en')
    cache = Path.home()/'.cache/huggingface/hub'/('models--Systran--faster-whisper-base.en' if language == 'en'
                                               else 'models--Systran--faster-whisper-base')/'snapshots'
    models = sorted(p for p in cache.glob('*') if (p/'model.bin').exists())
    import os
    import torch
    torch_lib = Path(torch.__file__).parent / "lib"
    _dll_dir = None
    if torch_lib.exists():
        os.environ['PATH'] = str(torch_lib) + ';' + os.environ.get('PATH', '')
        try:
            _dll_dir = os.add_dll_directory(str(torch_lib))
        except Exception:
            pass
    try:
        model = WhisperModel(str(models[-1]) if models else 'base', device='cuda', compute_type='float16',
                             local_files_only=True)
    except Exception:
        model = WhisperModel(str(models[-1]) if models else 'base', device='cpu', compute_type='int8',
                             cpu_threads=4, num_workers=1, local_files_only=True)
    tokenizer = Tokenizer(model.hf_tokenizer, model.model.is_multilingual, task='transcribe', language=language)
    audio = Path(manifest['output_file'])
    original_hash = file_hash(audio)
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio), '-ar', '16000', '-ac', '1',
                             '-f', 'f32le', '-'], capture_output=True, check=True, timeout=90)
    waveform = np.frombuffer(result.stdout, dtype=np.float32).copy()
    rows = []
    chunks = manifest['chunk_timeline']
    narration = (out/'narration.txt').read_text(encoding='utf-8')
    if ' '.join(' '.join(c['text'].split()) for c in chunks) != ' '.join(narration.split()):
        raise ValueError('Sentez parca metinleri onayli anlatimla uyusmuyor.')
    for chunk_id, chunk in enumerate(chunks):
        offset = chunk['start_sec']
        wave = waveform[round(offset*16000):round(chunk['end_sec']*16000)]
        if len(wave) > 30*16000:
            raise ValueError('Alignment parca suresi Whisper 30 saniye penceresini asiyor.')
        features = model.feature_extractor(wave)
        tokens = tokenizer.encode(' '+chunk['text'].strip())
        timings = model.find_alignment(tokenizer, [tokens], model.encode(features), features.shape[-1])[0]
        source_words = chunk['text'].split()
        if re.sub(r'\s+', '', ''.join(t['word'] for t in timings)) != re.sub(r'\s+', '', chunk['text']):
            raise ValueError('Whisper alignment tokenizer metni korumadi.')
        # Map tokenizer pieces (including punctuation) back to unchanged script words.
        parts, cursor = [], 0
        for timing in timings:
            size = len(re.sub(r'\s+', '', timing['word']))
            parts.append((cursor, cursor+size, timing))
            cursor += size
        cursor = 0
        for word in source_words:
            selected = [p[2] for p in parts if p[0] < cursor+len(word) and p[1] > cursor]
            if not selected:
                raise ValueError('Onayli kelime icin ses alignment bilgisi yok.')
            start = offset + float(selected[0]['start'])
            end = offset + float(selected[-1]['end'])
            if start > chunk['end_sec']+0.05 or end > chunk['end_sec']+0.05:
                raise ValueError('Alignment parcanin ses suresini asiyor.')
            rows.append({'id': len(rows), 'word': word, 'start': round(start, 3),
                         'end': round(min(end, chunk['end_sec']), 3), 'segment_id': chunk_id})
            cursor += len(word)
        print(f'Alignment: {chunk_id+1}/{len(chunks)}', flush=True)
    if file_hash(audio) != original_hash:
        raise ValueError('Alignment sirasinda ses degisti.')
    save_json(out/'voice_word_alignment.json', {'version': VERSION, 'audio_sha256': original_hash,
        'narration_sha256': file_hash(out/'narration.txt'), 'method': 'faster-whisper-cross-attention-forced-alignment',
        'language': language, 'words': rows, 'limit': 'Model-estimated word times; not sample-accurate phoneme boundaries.'})


if __name__ == '__main__':
    align_words(Path(sys.argv[1]))
