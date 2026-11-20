"""Stream remote ASR of finished TTS chunk groups while synthesis is still running.

Groups of consecutive chunks (~GROUP_SEC of audio, same 3600-sample gaps as the raw concat) are
sent to the VDS one at a time; per-group transcripts are cached by the chunk wav hashes, with
segment/word times relative to the group start. After the master is written, finish() writes
asr_groups/index.json (bound to the master hash); documentary_voice_audit.transcribe_full then
assembles voice_asr.json from the groups (offset = chunk start_sec) instead of a whole-file ASR.
Any error -> no index -> the old whole-file ASR runs. Off: DOCUMENTARY_STREAM_ASR=0."""
import hashlib
import json
import os
import queue
import threading
import time
from pathlib import Path

import numpy as np

VERSION = 'stream-asr-v1'
SR = 24000
GAP = 3600
ENV_OFF = 'DOCUMENTARY_STREAM_ASR'
ENV_GROUP = 'DOCUMENTARY_STREAM_ASR_GROUP_SEC'


def _target():
    t = os.environ.get('DOCUMENTARY_REMOTE_ASR', '').strip()
    if not t or t.lower() in ('0', 'off', 'false'):
        return ''
    if os.environ.get(ENV_OFF, '1').strip().lower() in ('0', 'off', 'false'):
        return ''
    return t


def _key(shas):
    return hashlib.sha256(json.dumps([VERSION, GAP, list(shas)]).encode()).hexdigest()[:24]


class StreamAsr:
    def __init__(self, out, target, language='en', group_sec=None, log=print):
        self.dir = Path(out) / 'asr_groups'
        self.dir.mkdir(parents=True, exist_ok=True)
        self.target, self.language, self.log = target, language, log
        self.group_sec = float(group_sec or os.environ.get(ENV_GROUP, '60'))
        self.q = queue.Queue()
        self.cur = []          # [(id, sha, start, data)]
        self.groups = []       # [{key, start_sec, chunk_ids, shas}]
        self.error = None
        self.t0 = time.time()
        self.stats = {'groups': 0, 'cached': 0, 'asr_sec': 0.0, 'first_done': None, 'events': []}
        self.thread = threading.Thread(target=self._worker, name='streamasr', daemon=True)
        self.thread.start()

    # ---- feeding (called from the synthesis loop; must never raise) ----
    def add(self, index, sha, start_sec, data):
        try:
            self.cur.append((index, sha, float(start_sec), data))
            span = (len(self.cur) - 1) * GAP + sum(len(c[3]) for c in self.cur)
            if span / SR >= self.group_sec:
                self._close()
        except Exception as e:
            self.error = self.error or repr(e)

    def _close(self):
        if not self.cur:
            return
        g = {'key': _key([c[1] for c in self.cur]), 'start_sec': self.cur[0][2],
             'chunk_ids': [c[0] for c in self.cur], 'shas': [c[1] for c in self.cur]}
        self.groups.append(g)
        self.q.put((g, self.cur))
        self.cur = []

    # ---- worker: one group at a time = at most one ASR job on the VDS ----
    def _worker(self):
        from documentary_voice_audit import remote_asr_rows
        while True:
            item = self.q.get()
            if item is None:
                return
            g, chunks = item
            if self.error:
                continue
            f = self.dir / (g['key'] + '.json')
            try:
                if f.is_file() and json.loads(f.read_text('utf-8')).get('key') == g['key']:
                    self.stats['cached'] += 1
                    continue
                parts = []
                for i, c in enumerate(chunks):
                    if i:
                        parts.append(np.zeros(GAP, dtype=np.float32))
                    parts.append(np.asarray(c[3], dtype=np.float32))
                pcm = np.concatenate(parts).tobytes()
                t = time.time()
                rows = remote_asr_rows(pcm, self.target, raw_f32_24k=True, guard=True)
                dt = time.time() - t
                tmp = f.with_suffix('.tmp')
                tmp.write_text(json.dumps({'key': g['key'], 'start_sec': g['start_sec'], 'rows': rows}), 'utf-8')
                os.replace(tmp, f)
                self.stats['groups'] += 1
                self.stats['asr_sec'] += dt
                self.stats['events'].append((round(time.time() - self.t0, 1), g['chunk_ids'][0], g['chunk_ids'][-1], round(dt, 1)))
                if self.stats['first_done'] is None:
                    self.stats['first_done'] = round(time.time() - self.t0, 1)
            except Exception as e:
                self.error = 'group %s: %s' % (g['chunk_ids'][:1], str(e)[:300])
                self.log('stream ASR off, whole-file fallback: %s' % self.error)

    def finish(self, master, master_sha, timeout=300):
        """Call after the master exists. True when the index (all groups) is written."""
        self._close()
        self.q.put(None)
        self.thread.join(timeout)
        if self.thread.is_alive() or self.error or not self.groups:
            if self.thread.is_alive():
                self.error = self.error or 'timeout'
            return False
        ids = [i for g in self.groups for i in g['chunk_ids']]
        index = {'version': VERSION, 'audio_sha256': master_sha, 'language': self.language,
                 'groups': [{'key': g['key'], 'start_sec': g['start_sec'], 'chunk_ids': g['chunk_ids']}
                            for g in self.groups], 'n_chunks': len(ids)}
        (self.dir / 'index.json').write_text(json.dumps(index), 'utf-8')
        return True


def maybe_start(out, language='en', log=print):
    t = _target()
    if not t or language != 'en':
        return None
    try:
        return StreamAsr(out, t, language, log=log)
    except Exception:
        return None


def assemble(audio, language, out, asr_version, model, file_hash, duration):
    """voice_asr.json-shaped dict from the cached groups, or None (caller falls back)."""
    d = Path(out) / 'asr_groups'
    idx = d / 'index.json'
    if not idx.is_file():
        return None
    index = json.loads(idx.read_text('utf-8'))
    if (index.get('version') != VERSION or index.get('audio_sha256') != file_hash(audio)
            or index.get('language') != language):
        return None
    rows = []
    for g in index['groups']:
        f = d / (g['key'] + '.json')
        if not f.is_file():
            return None
        blob = json.loads(f.read_text('utf-8'))
        off = float(g['start_sec'])
        for r in blob['rows']:
            rows.append({'start': r['start'] + off, 'end': r['end'] + off, 'text': r['text'],
                         'words': [{'start': w[1] + off, 'end': w[2] + off, 'word': w[0]} for w in r['words']]})
    if not rows:
        return None
    return {'version': asr_version, 'model': model, 'device': 'vds-cpu', 'compute_type': 'int8',
            'audio_sha256': file_hash(audio), 'language_requested': language,
            'processed_duration_sec': duration, 'text': ' '.join(r['text'] for r in rows), 'segments': rows}
