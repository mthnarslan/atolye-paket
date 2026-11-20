"""Bounded, chunk-targeted repair controller for the one-box voice pipeline."""
import difflib
import os
import json
import re
import time
from pathlib import Path

from documentary_voice_engine import (file_hash, load_json, pass_evidence_defects,
                                      pass_is_authentic, save_json, voice_output_dir,
                                      source_inventory_signature)

MAX_REPAIR_ROUNDS = 3
# A release authorization needs the reviewer's own evidence behind it.
PASSING_VERDICTS = ('PASS', 'PASS_DEGRADED')


def _audit_release_allowed(audit):
    """True only when a PASS carries its evidence, its hashes and clean criteria."""
    if not isinstance(audit, dict) or audit.get('verdict') not in PASSING_VERDICTS:
        return False
    review = audit.get('gemini_audio') or {}
    if pass_evidence_defects(review):
        return False
    if review.get('text_completeness') != 'PASS' or review.get('reference_voice_match') != 'PASS':
        return False
    if review.get('verdict') not in PASSING_VERDICTS:
        return False
    return True


def comparison_tokens(text):
    # Treat symbolic W_4 / W4 and spoken W four alike, without dropping numbers.
    text = re.sub(r'([A-Za-z])_?([0-9])\b', r'\1 \2', text)
    digits = dict(zip('0123456789', 'zero one two three four five six seven eight nine'.split()))
    return [digits.get(token, token) for token in re.findall(r"\w+", text.casefold())]


def repair_identity(chunks, reference, language, engine):
    return engine.repair_identity(chunks, reference, language)


def validated_overrides(base_chunks, state):
    effective = list(base_chunks)
    options = {}
    overrides = state.get('overrides', {}) if isinstance(state, dict) else {}
    for key, value in overrides.items():
        if not str(key).isdigit():
            continue
        index = int(key)
        if not 0 <= index < len(base_chunks) or not isinstance(value, dict):
            continue
        text, seed = value.get('text'), value.get('seed')
        # A very short chunk that kept drifting to another voice is merged into
        # its neighbour: the neighbour's override carries both texts, this one
        # becomes empty (skipped by synthesis; chunk ids stay stable).
        into = value.get('merged_into')
        if (text == '' and type(into) is int and abs(into - index) == 1
                and 0 <= into < len(base_chunks) and type(seed) is int):
            if overrides.get(str(into), {}).get('merged_from') == index:
                effective[index] = ''
            continue
        if (not isinstance(text, str) or not text.strip() or len(text.split()) > 45
                or type(seed) is not int or not 0 <= seed <= 10000):
            continue
        reference_text = base_chunks[index]
        donor = value.get('merged_from')
        if type(donor) is int and abs(donor - index) == 1 and 0 <= donor < len(base_chunks):
            reference_text = (base_chunks[donor] + ' ' + reference_text if donor < index
                              else reference_text + ' ' + base_chunks[donor])
        similarity = difflib.SequenceMatcher(None, comparison_tokens(reference_text),
                                              comparison_tokens(text), autojunk=False).ratio()
        if similarity < 0.72:
            continue
        effective[index] = ' '.join(text.split())
        options[str(index)] = {'seed': seed}
    return effective, options


NUMBER_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
    'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12,
    'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
    'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40,
    'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
}


def normalized_number_tokens(words):
    """Rewrite spoken numbers into one canonical form, or return None.

    Two transcriptions of the same audio write the same quantity in different
    ways: the reviewer says "sixteen hundred" where Whisper says "one 600".
    Comparing those as plain words hides a real defect, so the number words
    are folded into a single numeric token before the two are compared.

    None means the window holds something this cannot normalise (a decimal
    read like "seven point zero five"), and the caller must stay careful.
    """
    out = []
    index = 0
    while index < len(words):
        word = words[index]
        if word in NUMBER_WORDS:
            value = NUMBER_WORDS[word]
            index += 1
            if index < len(words) and words[index] == 'hundred':
                value *= 100
                index += 1
            elif index < len(words) and words[index] == 'thousand':
                value *= 1000
                index += 1
            elif (value == 1 and index < len(words) and words[index].isdigit()
                    and len(words[index]) == 3):
                # "one 600" is how a transcriber writes sixteen hundred.
                value = 1000 + int(words[index])
                index += 1
            out.append(str(value))
            continue
        if word.isdigit():
            out.append(str(int(word)))
            index += 1
            continue
        if word in ('point', 'oh', 'pm', 'am', 'p', 'm'):
            # A clock time or a decimal: no single canonical form.
            return None
        out.append(word)
        index += 1
    return out


def _asr_window(manifest, start, end, pad=0.6):
    """The independent Whisper transcript of one time window, as words."""
    out = Path(manifest['output_file']).parent
    asr = load_json(out/'voice_asr.json') or {}
    segments = asr.get('segments') or []
    words = []
    for segment in segments:
        low, high = segment.get('start'), segment.get('end')
        if type(low) not in (int, float) or type(high) not in (int, float):
            continue
        if high < start - pad or low > end + pad:
            continue
        words.extend(comparison_tokens(segment.get('text', '')))
    return words


def _is_spelled_out(words):
    """True when the words are a single word written out letter by letter.

    The reviewer reports these as "T-H-E-R-E-F-O-R" or "A-N-D": the letters
    of one word, each on its own. The acceptance policy lists isolated
    spelling-out that does not obscure the meaning as an acceptable
    observation, not a narration defect.
    """
    if not words or len(words) < 3:
        return False
    return all(len(word) == 1 and word.isalpha() for word in words)


def _contains_sequence(haystack, needle):
    """True when the word sequence 'needle' appears in 'haystack'.

    A substring test is not enough here: "west" is a substring of
    "midwest", and a one-word expectation like "and" occurs in almost any
    window. The comparison is on whole words, in order.
    """
    if not needle or len(needle) > len(haystack):
        return False
    for start in range(len(haystack) - len(needle) + 1):
        if haystack[start:start + len(needle)] == needle:
            return True
    return False


def _asr_contradicts(manifest, issue, chunk_text):
    """True when the independent ASR does not show the reported problem.

    The reviewer is a model reading audio; the ASR is a second, independent
    transcription of the same audio. The live run used to repair whatever the
    model reported, and in three rounds that meant re-synthesising chunks for
    things the transcript does not show: "Midwest" heard as "West.", "AND"
    heard as "A-N-D", "7:05 PM" heard as "7.05 pm". Those repairs changed the
    audio without fixing anything and cost a full audit round each time.

    The rule is narrow on purpose. The finding is dropped only when the
    second transcription shows the approved words in that window and does not
    show the reported ones: that is a difference between two readings of the
    same speech, which the acceptance policy calls a warning. Everything
    else keeps the finding, so a real defect is never dropped.
    """
    start, end = issue.get('start_sec'), issue.get('end_sec')
    if type(start) not in (int, float) or type(end) not in (int, float):
        return False
    heard = comparison_tokens(issue.get('heard', ''))
    expected = comparison_tokens(issue.get('expected', ''))
    window = _asr_window(manifest, start, end)
    if not window:
        # No independent transcript for this window: keep the reviewer's
        # finding rather than silently dropping a real problem.
        return False
    # The two transcriptions have to be compared in the same notation.
    heard_n = normalized_number_tokens(heard)
    expected_n = normalized_number_tokens(expected)
    window_n = normalized_number_tokens(window)
    if window_n is None or heard_n is None or expected_n is None:
        # A number this cannot normalise is in the way. The two
        # transcriptions cannot be compared reliably, so the reviewer's
        # finding is kept.
        return False
    if not expected_n:
        return False
    expected_present = _contains_sequence(window_n, expected_n)
    if not expected_present:
        # The approved words are not in the transcript at all. That may be a
        # real omission, and the reviewer is the only evidence for it.
        return False
    # The approved words are there. Now: does the transcript also show the
    # words the reviewer reported hearing?
    if _contains_sequence(window_n, heard_n):
        # The transcript shows the same reported words. The finding stands:
        # a repeated or added word is visible to both transcriptions.
        return False
    if _is_spelled_out(heard_n):
        # The reviewer heard the word spelled out letter by letter
        # ("T-H-E-R-E-F-O-R") while the transcript heard the word itself
        # ("therefore"). The acceptance policy lists isolated spelling-out
        # as an acceptable observation.
        return True
    # The transcript has the approved words and not the reported ones. The
    # reviewer is describing a difference between two readings of the same
    # speech ("Midwest" vs "West.", "AND" vs "A-N-D"), which the
    # acceptance policy calls a warning, not a defect. The independent
    # transcript does not support it.
    return True


def repair_targets(manifest, audit):
    """Return only chunks supported by timed, explicit Gemini text-failure evidence."""
    review = audit.get('gemini_audio') or {}
    if ((audit.get('verdict') != 'FAIL' and review.get('text_completeness') != 'FAIL')
            or review.get('reference_voice_match') != 'PASS'):
        return {}
    targets = {}
    for issue in review.get('issues', []):
        if not isinstance(issue, dict) or issue.get('kind') != 'text':
            continue
        start, end = issue.get('start_sec'), issue.get('end_sec')
        if type(start) not in (int, float) or type(end) not in (int, float) or start < 0 or end <= start:
            continue
        candidates = [chunk for chunk in manifest.get('chunk_timeline', [])
                      if chunk.get('start_sec', 0) < end + 0.2 and chunk.get('end_sec', 0) > start - 0.2]
        # A reported addition can be at the end of the preceding chunk.
        # Preserve nearby timed chunks; use the exact phrase alone for distant timestamp drift.
        expected_words = comparison_tokens(issue.get('expected', ''))
        expected = ' '.join(expected_words)
        timeline = manifest.get('chunk_timeline', [])
        all_words, owners = [], []
        for chunk in timeline:
            part = comparison_tokens(chunk.get('text', ''))
            all_words.extend(part)
            owners.extend([chunk['id']]*len(part))
        positions = [n for n in range(len(all_words)-len(expected_words)+1)
                     if expected_words and all_words[n:n+len(expected_words)] == expected_words]
        boundary_ids = set()
        if len(positions) == 1:
            n = positions[0]
            ids = set(owners[n:n+len(expected_words)])
            matched = [c for c in timeline if c['id'] in ids]
            if len(matched) <= 4:
                nearby = [c for c in candidates if any(abs(c['id']-m['id']) <= 1 for m in matched)]
                boundary_ids = {c['id'] for c in nearby
                                if min(c['end_sec'], end)-max(c['start_sec'], start) >= 0.35}
                candidates = [c for c in timeline if c['id'] in ids | boundary_ids]
        if len(candidates) > 4:
            continue
        for chunk in candidates:
            words = set(comparison_tokens(chunk.get('text', '')))
            quote = set(comparison_tokens(issue.get('expected', '') + ' ' + issue.get('heard', '')))
            short_matches = [c for c in candidates if expected in set(comparison_tokens(c.get('text', '')))]
            short_expected = len(expected.split()) == 1 and expected in words and len(short_matches) == 1
            if chunk['id'] in boundary_ids or short_expected or len(words & quote) >= min(2, len(words)):
                if _asr_contradicts(manifest, issue, chunk.get('text', '')):
                    # The independent transcript does not show this problem.
                    # Repairing it would change the audio for nothing.
                    continue
                targets.setdefault(str(chunk['id']), {'chunk': chunk, 'issues': []})['issues'].append(issue)
    return targets


VOICE_MAX_TARGETS = 4          # more drifting chunks than this is systemic, not a seed problem
VOICE_MERGE_MAX_WORDS = 8      # a chunk this short that drifts twice is merged into a neighbour


def voice_targets(manifest, audit):
    """Chunks the reviewer flagged (timed, kind=voice) as drifting off the reference voice."""
    review = audit.get('gemini_audio') or {}
    if review.get('reference_voice_match') != 'FAIL':
        return {}
    targets = {}
    for issue in review.get('issues', []):
        if not isinstance(issue, dict) or issue.get('kind') != 'voice':
            continue
        start, end = issue.get('start_sec'), issue.get('end_sec')
        if type(start) not in (int, float) or type(end) not in (int, float) or start < 0 or end <= start:
            continue
        for chunk in manifest.get('chunk_timeline', []):
            overlap = min(chunk['end_sec'], end) - max(chunk['start_sec'], start)
            if overlap >= min(0.3, (end - start) / 2):
                targets.setdefault(str(chunk['id']), {'chunk': chunk, 'issues': []})['issues'].append(issue)
    return targets if 0 < len(targets) <= VOICE_MAX_TARGETS else {}


def sentence_count(text):
    return len(re.findall(r'[.!?:;]+(?:\s|$)', text.strip() + ' '))


def propose_text(current, issues, flash_json, split=False):
    prompt = (
        'Make the smallest safe edit to this exact approved narration chunk to address the reported audible error. '
        'Keep all facts, names, quantities and sentence meaning unchanged. Normalize misread uppercase words or '
        'mathematical notation into natural spoken wording only when supported by the issue. No additions, '
        'If unwanted speech is appended to a chunk ending in a comma, replace that final comma with a period '
        'to give TTS a clear stop; keep every approved word. '
        'summaries, stylistic rewrite, or commentary. If unclear, return the original unchanged. '
        + (
            # Pocket ignores the seed: the same text gives the same audio, so a repeated or swapped word comes back
            # on every retry (Mayfield "thirty thousand or forty thousand" x3). Only new wording changes the audio.
            'This voice engine always speaks the same text the same way, so the wording around the error MUST change '
            '(same meaning, e.g. "thirty thousand or forty thousand feet" -> "thirty or forty thousand feet"); never '
            'return the original. '
            if os.environ.get('DOCUMENTARY_VOICE_ENGINE', '').strip().lower() == 'pocket' else '')
        + (
            # The same chunk failed again after a reword: Pocket skips or garbles long clauses, so shorten them.
            'A previous reword of this chunk still failed. Now split the sentence around the error into two or '
            'three short sentences (each under twelve words, same facts, same order, full stops instead of '
            'colons or long clauses). '
            if split else '')
        + 'Return raw JSON {"corrected_text":"..."}.\n'
        + json.dumps({'approved_current_chunk': current, 'timed_audio_issues': [
            {k: issue.get(k) for k in ('start_sec', 'end_sec', 'expected', 'heard', 'reason')}
            for issue in issues]}, ensure_ascii=False)
    )
    response = flash_json(prompt)
    value = response.get('corrected_text') if isinstance(response, dict) else None
    if not isinstance(value, str):
        return None
    value = ' '.join(value.split())
    if not value or value == ' '.join(current.split()) or len(value.split()) > 45:
        return None
    if split and sentence_count(value) <= sentence_count(current):
        return None
    score = difflib.SequenceMatcher(None, comparison_tokens(current),
                                    comparison_tokens(value), autojunk=False).ratio()
    return value if score >= 0.72 else None


def apply_targeted_repair(manifest, audit, engine, progress, state):
    targets = repair_targets(manifest, audit)
    voice_mode = False
    if not targets:
        targets = voice_targets(manifest, audit)
        voice_mode = bool(targets)
    if not targets:
        return None
    base = list(manifest.get('approved_chunks') or manifest['chunks'])
    current = list(manifest['chunks'])
    identity = repair_identity(base, manifest['reference_audio'], manifest.get('language', 'en'), engine)
    if state.get('identity') != identity:
        state = {'version': 1, 'identity': identity, 'overrides': {}}
    overrides = state.setdefault('overrides', {})
    changes, options = [], dict(manifest.get('chunk_options') or {})
    # Each target needs its own Flash call to propose a corrected wording.
    # Those calls are independent of each other, and the live run measured
    # them at 31-42 s each, all issued one after another: three targets
    # cost 110 s of pure waiting. They run concurrently instead, so the
    # round costs one call's time rather than the sum.
    eligible = []
    for key, target in targets.items():
        index = int(key)
        if not 0 <= index < len(current) or current[index] != target['chunk'].get('text'):
            continue
        eligible.append((key, index, target))
    # A chunk that already carries a rewrite and failed again is split, not reworded again.
    resplit = {key for key, index, _ in eligible
               if overrides.get(key, {}).get('text') not in (None, base[index])}
    proposals = {}
    # A voice drift keeps the approved wording: only the seed changes, no Flash call.
    if eligible and not voice_mode:
        import concurrent.futures
        from adaptive_governor import get_governor
        capacity = max(1, int(get_governor().config("flash")["ceiling"]))
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(eligible), capacity)) as pool:
            futures = {pool.submit(propose_text, current[index], target['issues'],
                                   engine.flash_json, key in resplit): key
                       for key, index, target in eligible}
            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                try:
                    proposals[key] = future.result()
                except Exception:
                    proposals[key] = None
    for key, index, target in eligible:
        fixed = proposals.get(key)
        prior = overrides.get(key, {})
        old_seed = prior.get('seed', 42) if type(prior.get('seed', 42)) is int else 42
        seed = old_seed if fixed else (old_seed + 53) % 10001
        new_text = fixed or current[index]
        if new_text == current[index] and seed == old_seed:
            seed = (seed + 53) % 10001
        merged = None
        if voice_mode:
            seed = (old_seed + 53) % 10001
            seeded_before = prior.get('seed') is not None and prior.get('seed') != 42
            neighbour = next((n for n in (index + 1, index - 1)
                              if 0 <= n < len(current) and current[n].strip()
                              and overrides.get(str(n), {}).get('merged_into') is None), None)
            if (seeded_before and len(new_text.split()) <= VOICE_MERGE_MAX_WORDS and neighbour is not None
                    and len((current[neighbour] + ' ' + new_text).split()) <= 45):
                merged = neighbour
        if merged is not None:
            host_text = (new_text + ' ' + current[merged]) if merged > index else (current[merged] + ' ' + new_text)
            host_seed = overrides.get(str(merged), {}).get('seed', 42)
            overrides[str(merged)] = {'text': host_text, 'seed': host_seed, 'merged_from': index}
            current[merged] = host_text
            options[str(merged)] = {'seed': host_seed}
            overrides[key] = {'text': '', 'seed': seed, 'merged_into': merged}
            current[index] = ''
            options.pop(key, None)
            changes.append({'chunk_id': index, 'before': target['chunk']['text'], 'after': '',
                            'merged_into': merged, 'seed': host_seed, 'issues': [
                                {k: i.get(k) for k in ('start_sec', 'end_sec', 'expected', 'heard', 'reason')}
                                for i in target['issues']]})
            continue
        overrides[key] = {'text': new_text, 'seed': seed}
        current[index] = new_text
        options[key] = {'seed': seed}
        changes.append({'chunk_id': index, 'before': target['chunk']['text'], 'after': new_text,
                        'seed': seed, 'issues': [{k: i.get(k) for k in (
                            'start_sec', 'end_sec', 'expected', 'heard', 'reason')} for i in target['issues']]})
    if not changes:
        return None
    progress('Duzeltme: yalniz zaman damgasiyla eslesen parcalar yenileniyor')
    out = Path(manifest['output_file']).parent
    for path, expected_hash in [(manifest['reference_audio'], manifest.get('reference_sha256')),
                                (manifest['script_path'], manifest.get('script_sha256')),
                                (manifest['output_file'], manifest.get('output_sha256'))]:
        if file_hash(path) != expected_hash:
            raise ValueError('Repair inputs changed since the audited generation.')
    failed_audio_hash = manifest['output_sha256']
    evidence_dir = out/'repair_audits'/failed_audio_hash
    evidence_dir.mkdir(parents=True, exist_ok=True)
    save_json(evidence_dir/'voice_audit.json', audit)
    save_json(evidence_dir/'voice_manifest.json', manifest)
    save_json(out/'voice_audit.json', {'verdict': 'RUNNING', 'next_step_allowed': False,
                                      'reason': 'Repair in progress; previous audit is stale.'})
    save_json(out/'voice_progress.json', {'status': 'REPAIRING', 'next_step_allowed': False})
    # Preserve the original master/manifest once, before the first automatic repair.
    import shutil
    backup = out/'pre_repair'
    backup.mkdir(exist_ok=True)
    for name in ('master_voiceover.wav', 'voice_manifest.json', 'narration.txt'):
        source = out/name
        if source.exists() and not (backup/name).exists():
            shutil.copy2(source, backup/name)
    revised = engine.generate_full_voiceover(current, manifest['reference_audio'], out,
                                              manifest.get('language', 'en'), progress,
                                              chunk_options=options)
    revised.update({k: v for k, v in manifest.items() if k not in revised})
    revised['chunks'] = current
    revised['approved_chunks'] = base
    revised['chunk_options'] = {**(manifest.get('chunk_options') or {}), **options}
    revised['repair_round'] = manifest.get('repair_round', 0) + 1
    revised['repair_changes'] = changes
    # The previous round's audit and manifest are kept so the next audit can
    # carry the verdict for the segments whose audio did not change instead of
    # paying the model again for the same bytes.
    revised['previous_audit_path'] = str(evidence_dir/'voice_audit.json')
    revised['previous_manifest_path'] = str(evidence_dir/'voice_manifest.json')
    (out/'narration.txt').write_text('\n'.join(c for c in current if c.strip()), encoding='utf-8')
    revised['narration_sha256'] = file_hash(out/'narration.txt')
    save_json(out/'voice_repair_state.json', state)
    save_json(out/'voice_manifest.json', revised)
    save_json(out/'voice_audit.json', {'verdict': 'RUNNING', 'version': 'voice-audit-v1',
                                      'reason': 'Targeted audio repair changed the master.'})
    return revised, changes


def _run_with_repair(engine, auditor, folder, progress=print, max_rounds=MAX_REPAIR_ROUNDS):
    if type(max_rounds) is not int or not 0 <= max_rounds <= MAX_REPAIR_ROUNDS:
        raise ValueError('Repair rounds must be within the hard configured limit.')
    # The round budget is policy, not code: it comes from the audit config so
    # it can be changed without touching the control flow.
    config = load_json(Path(__file__).with_name('documentary_voice_audit_config.json')) or {}
    policy_rounds = (config.get('loop_guard') or {}).get('max_repair_rounds')
    if type(policy_rounds) is int and 0 <= policy_rounds <= MAX_REPAIR_ROUNDS:
        max_rounds = min(max_rounds, policy_rounds)
    folder = Path(folder).expanduser().resolve(strict=True)
    out = voice_output_dir(folder)
    out.mkdir(parents=True, exist_ok=True)
    previous_manifest = load_json(out/'voice_manifest.json')
    previous_audit = load_json(out/'voice_audit.json')
    inventory_signature = source_inventory_signature(folder)
    if _reusable_completed_pass(engine, folder, out, inventory_signature, previous_manifest, previous_audit):
        cached = dict(previous_manifest)
        cached['reused_completed_result'] = True
        cached['generated_chunks'] = 0
        cached['reused_chunks'] = cached.get('total_chunks', 0)
        cached['synthesis_time_sec'] = 0.0
        progress('Onceden dogrulanmis ses bulundu; Flash ve Sopro yeniden calistirilmadi.')
        engine.save_json(out/'voice_progress.json', {
            'status': 'SUCCESS', 'audio_ready': True, 'audit_verdict': 'PASS',
            'next_step_allowed': True, 'output_file': cached['output_file'],
            'reused_completed_result': True, 'flash_calls': 0, 'synthesized_chunks': 0})
        return cached, previous_audit
    save_json(out/'voice_audit.json', {'verdict': 'RUNNING', 'version': auditor.VERSION,
                                      'next_step_allowed': False})
    if _reusable_generated_result(engine, folder, out, inventory_signature, previous_manifest):
        manifest = dict(previous_manifest)
        manifest.update(generated_chunks=0, reused_chunks=manifest.get('total_chunks', 0),
                        reused_generated_audio=True, synthesis_time_sec=0.0)
        progress('Mevcut tam ses korundu; yalniz eksik/guncel ses kontrolu calisiyor.')
    else:
        manifest = engine.run_step1(folder, progress)
    state = load_json(out/'voice_repair_state.json') or {}
    history = []
    audit = auditor.run_audit(manifest, progress)
    for round_number in range(1, max_rounds + 1):
        if audit.get('next_step_allowed'):
            break
        repaired = apply_targeted_repair(manifest, audit, engine, progress, state)
        if not repaired:
            break
        manifest, changes = repaired
        state = load_json(out/'voice_repair_state.json') or {}
        history.append({'round': round_number, 'changes': changes,
                        'failed_audio_hash': audit.get('hashes', {}).get('audio'),
                        'new_audio_hash': manifest.get('output_sha256')})
        save_json(out/'voice_repair_history.json', history)
        audit = auditor.run_audit(manifest, progress)
    audit['repair_history'] = history
    audit['repair_rounds'] = len(history)
    # A claimed PASS with stale hashes is never an authorization for downstream work.
    paths = {'audio': manifest['output_file'], 'reference': manifest['reference_audio'],
             'source': manifest['script_path'], 'narration': out/'narration.txt'}
    valid_hashes = all(audit.get('hashes', {}).get(k) == file_hash(path) for k, path in paths.items())
    if audit.get('verdict') == 'PASS' and not valid_hashes:
        audit['verdict'] = 'UNVERIFIED'
        audit['summary'] = 'Son dosya hashleri kontrol kanitiyla eslesmiyor.'
    review = audit.get('gemini_audio') or {}
    strict_checks = (review.get('text_completeness') == 'PASS'
                     and review.get('reference_voice_match') == 'PASS'
                     and review.get('verdict') in PASSING_VERDICTS)
    # Strict check: all required criteria must pass; no autonomous override
    audit['next_step_allowed'] = (audit.get('verdict') in PASSING_VERDICTS
                                  and strict_checks and valid_hashes)
    if audit['next_step_allowed'] and not _audit_release_allowed(audit):
        # A claimed PASS without the reviewer's evidence is not an approval.
        audit['verdict'] = 'UNVERIFIED'
        audit['next_step_allowed'] = False
        audit['integrity_defects'] = pass_evidence_defects(review)
    if not audit['next_step_allowed']:
        audit['summary'] = (audit.get('summary') or 'Ses QA PASS degil.') + (
            ' Sonraki adim kilitli; eslesmeyen bulgu veya sinirli duzeltme turu nedeniyle otomatik PASS verilmedi.')
    save_json(out/'voice_manifest.json', manifest)
    save_json(out/'voice_audit.json', audit)
    save_json(out/'voice_progress.json', {
        'status': 'SUCCESS' if audit['next_step_allowed'] else audit.get('verdict', 'UNVERIFIED'),
        'audio_ready': True, 'audit_verdict': audit.get('verdict'),
        'next_step_allowed': audit['next_step_allowed'], 'repair_rounds': len(history),
        'output_file': manifest['output_file'],
        'scope': 'reference_voice_similarity_full_audio_text_and_technical'})
    return manifest, audit


def _reusable_completed_pass(engine, folder, out, inventory_signature, manifest, audit):
    """Reuse only a complete PASS whose current source and output bytes still match its receipts."""
    if not isinstance(manifest, dict) or not isinstance(audit, dict):
        return False
    audio = Path(out/'master_voiceover.wav')
    reference = Path(manifest.get('reference_audio', ''))
    source = Path(manifest.get('script_path', ''))
    narration = out/'narration.txt'
    if (audit.get('verdict') not in PASSING_VERDICTS or not audit.get('next_step_allowed')
            or manifest.get('input_folder') != str(folder)
            or manifest.get('output_file') != str(audio)
            or manifest.get('source_inventory_sha256') != inventory_signature
            or not audio.is_file() or not source.is_file() or not reference.is_file() or not narration.is_file()):
        return False
    review = audit.get('gemini_audio') or {}
    strict_checks = (review.get('text_completeness') == 'PASS'
                     and review.get('reference_voice_match') == 'PASS'
                     and review.get('verdict') in PASSING_VERDICTS)
    # Strict check: all required criteria must pass; no autonomous override
    if not strict_checks:
        return False
    # A cached approval must carry the reviewer's own evidence, otherwise a
    # hand-written verdict file would keep unlocking the next stage forever.
    if pass_evidence_defects(review):
        return False
    if audit.get('gemini_audio', {}).get('hashes') and audit.get('gemini_audio', {}).get('hashes') != audit.get('hashes'):
        return False
    hashes = audit.get('hashes', {})
    actual = {'audio': engine.file_hash(audio), 'source': engine.file_hash(source),
              'reference': engine.file_hash(reference), 'narration': engine.file_hash(narration)}
    return (hashes == actual and manifest.get('output_sha256') == actual['audio']
            and manifest.get('script_sha256') == actual['source']
            and manifest.get('reference_sha256') == actual['reference'])


def _reusable_generated_result(engine, folder, out, inventory_signature, manifest):
    if not isinstance(manifest, dict):
        return False
    if (manifest.get('input_folder') != str(folder)
            or manifest.get('source_inventory_sha256') != inventory_signature
            or manifest.get('output_file') != str(out/'master_voiceover.wav')
            or not (out/'narration.txt').is_file()):
        return False
    # Audio voiced from an outdated narration plan (the script parser changed)
    # is not reused; it would be audited and repaired chunk by chunk instead.
    scan = engine.load_json(out/'source_selection.json')
    if not scan or manifest.get('plan_key') != engine.narration_plan_key(scan):
        return False
    try:
        return (engine.file_hash(out/'narration.txt') == manifest.get('narration_sha256')
                and all(engine.file_hash(manifest[path]) == manifest[sha] for path, sha in (
            ('output_file', 'output_sha256'), ('script_path', 'script_sha256'),
            ('reference_audio', 'reference_sha256'))))
    except (KeyError, OSError):
        return False


def run_with_repair(engine, auditor, folder, progress=print, max_rounds=MAX_REPAIR_ROUNDS):
    """Keep generation, repair, and final approval under one exclusive folder lock."""
    import msvcrt
    out = voice_output_dir(Path(folder).expanduser().resolve(strict=True))
    out.mkdir(exist_ok=True)
    locked = False
    lock_file = out / 'pipeline.lock'
    try:
        lock = lock_file.open('a+b')
    except (OSError, PermissionError):
        time.sleep(0.5)
        try:
            lock = lock_file.open('a+b')
        except (OSError, PermissionError):
            raise RuntimeError('This folder already has an active generation/audit/repair run.') from None

    try:
        try:
            lock.seek(0)
            if lock.read(1) == b'':
                lock.write(b'0')
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            locked = True
        except (OSError, PermissionError):
            raise RuntimeError('This folder already has an active generation/audit/repair run.') from None

        folder = Path(folder).expanduser().resolve(strict=True)
        owner = load_json(out / 'voice_source.json')
        if owner and owner.get('input_folder') != str(folder):
            raise ValueError('A different source folder already owns this Desktop output name. Rename the source folder.')
        if not owner:
            # film_settings.json is the bridge's own (the profile, written
            # before stage 1), so a new wildlife film is not a foreign folder.
            existing = [p for p in out.iterdir() if p.name not in {'pipeline.lock', 'run.lock', 'film_settings.json'}]
            if existing:
                raise ValueError('Desktop output folder is not empty and has no source identity; existing files were preserved.')
            save_json(out / 'voice_source.json', {'input_folder': str(folder)})
        try:
            return _run_with_repair(engine, auditor, folder, progress, max_rounds)
        except Exception as error:
            failed = {'verdict': 'UNVERIFIED', 'next_step_allowed': False,
                      'error_type': type(error).__name__,
                      'error_detail': str(error),
                      'summary': 'Uretim/duzeltme tamamlanamadi; sonraki adim kapali.'}
            save_json(out / 'voice_audit.json', failed)
            save_json(out / 'voice_progress.json', {'status': 'UNVERIFIED', 'next_step_allowed': False})
            raise
    finally:
        if locked:
            try:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                pass
        try:
            lock.close()
        except Exception:
            pass
