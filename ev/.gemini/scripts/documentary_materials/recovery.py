"""One bounded, evidence-backed camera-footage recovery batch for failed shots."""
from concurrent.futures import CancelledError, ThreadPoolExecutor
import math
from pathlib import Path
import re
import subprocess
import threading
import time

from . import footage, profiles, sources, window_index
from .control import check_cancelled, set_context
from .io import api, digest, event, load, save, sha

# A recovery batch is found again while its shots, this version, this
# module and the source policy (catalog_policy.py) are what they were,
# the module as a syntax tree (code_identity.py), so a comment does not
# search again. Bump the version when a change elsewhere has to reach it.
RECOVERY_VERSION = 1


def _admit(classified, originals):
    assets = []
    hashes = {}
    seen = set()
    for value in classified:
        original = originals.get(value.get("id"))
        # An invented or repeated id is skipped, not fatal: the other
        # classifications in the answer are still good.
        if original is None or original["id"] in seen:
            continue
        seen.add(original["id"])
        if value.get("category") != "VIDEO" or value.get("usable") is not True:
            continue
        path = original.get("path", "")
        if not Path(path).is_file():
            continue
        if path not in hashes:
            hashes[path] = sha(path)
        if hashes[path] != original.get("sha256") or int(original.get("native_height") or 0) < 1080:
            continue
        a, b = float(original["start"]), float(original["end"])
        if not math.isfinite(a) or not math.isfinite(b) or not 0 <= a < b:
            continue
        # Keep provenance from probed sources; model output may only describe it.
        assets.append({**original, "category": "VIDEO", "usable": True,
            **{k: value.get(k) for k in ("description", "keywords", "problems", "tone", "composition",
                 "classification_receipt", "classification_sampling", "sample_contact")},
            "required_context_label": "Illustrative live footage",
            "source_context": "Illustrative live camera footage; not authenticated historical event footage. Source: " + original["source_url"]})
    return assets


# The per-sentence search runs in English and in this many of the profile's
# other languages (its first ones): seven languages a line cost a median
# 5 min a search on TOPIC_2, and the extra languages rarely added footage.
SENTENCE_LANGUAGES = 1

_INFLIGHT = {}
_INFLIGHT_LOCK = threading.Lock()


def _sentence_key(shot):
    return re.sub(r"\s+", " ", str(shot.get("narration") or "")).strip().lower()


def _empty_ledger(out):
    return Path(out) / "source_recovery" / "empty_sentences.json"


def search_sources_for_shots(failed_shots, out, max_sources=40):
    """New footage searched for the sentences the catalog could not cover.

    The catalog is searched once, from the topic, before the plan exists.
    A sentence about an engine-room generator or a police roadblock then
    finds nothing to cut, and the shot fails review after review. Here
    each failed sentence gets its own footage query; the new windows are
    fetched, classified and handed to those shots, and the per-shot
    review still decides.

    A sentence whose earlier search found no source is not searched again
    (TOPIC_1: 125 of 206 in-queue searches found none, none passed). One
    shot of a scene whose search is already running waits for it and takes
    its footage instead of starting a second search.
    """
    out = Path(out)
    empty = set(load(_empty_ledger(out)).get("sentences") or []) if _empty_ledger(out).is_file() else set()
    skipped = [s["shot_id"] for s in failed_shots if _sentence_key(s) and _sentence_key(s) in empty]
    if skipped:
        event(out, "shot_source_search_skipped", shots=skipped, reason="an earlier search of the sentence found no source")
        failed_shots = [s for s in failed_shots if s["shot_id"] not in skipped]
    if not failed_shots:
        return []
    if len(failed_shots) != 1 or failed_shots[0].get("scene_id") is None:
        return _search_sources(failed_shots, out, max_sources)
    key = (str(out.resolve()), failed_shots[0]["scene_id"])
    with _INFLIGHT_LOCK:
        holder = _INFLIGHT.get(key)
        owner = holder is None
        if owner:
            holder = _INFLIGHT[key] = {"done": threading.Event(), "assets": None, "shot": failed_shots[0]["shot_id"]}
    if not owner:
        while not holder["done"].wait(1):
            check_cancelled(out)
        if holder["assets"] is not None:
            event(out, "shot_source_search_shared", shot=failed_shots[0]["shot_id"], with_shot=holder["shot"],
                  scene=failed_shots[0]["scene_id"], assets=len(holder["assets"]))
            return list(holder["assets"])
        return _search_sources(failed_shots, out, max_sources)
    try:
        holder["assets"] = _search_sources(failed_shots, out, max_sources)
        return holder["assets"]
    finally:
        with _INFLIGHT_LOCK:
            _INFLIGHT.pop(key, None)
        holder["done"].set()


def _search_sources(failed_shots, out, max_sources):
    sources.ensure_pot_server(out)
    shots = [{"shot_id": s["shot_id"], "narration": s.get("narration"),
              "visual_goal": (s.get("story_plan") or {}).get("visual_goal"), "problem": s.get("problem")}
             for s in failed_shots]
    # "nonbbc-known" keys out the searches made while the .nonbbc markers
    # still counted as fetched sources and every marked video was skipped.
    folder = out / "source_recovery" / ("search_" + digest([shots, "nonbbc-known"])[:12])
    manifest = folder / "result.json"
    if manifest.is_file() and load(manifest).get("status") == "COMPLETE":
        return load(manifest)["assets"]
    folder.mkdir(parents=True, exist_ok=True)
    # The wildlife profile searches each sentence in English on the BBC
    # channels first and then in its other languages on YouTube, and takes
    # more results per query; the default profile searches as before.
    production = profiles.for_run(out)
    sources.restrict_channels(production, out)
    sources.relax_channels()
    languages = tuple(production.get("languages") or ())[:SENTENCE_LANGUAGES]
    # Three sources a shot can carry its line (a source gives up to three
    # cuts); the wildlife profile's 150 cap fetched ~90 sources for 20 shots
    # and the end phase ran past 20 minutes on downloads.
    max_sources = min(production.get("max_sources", max_sources), max(6, 3 * len(failed_shots)))
    localized = (' Also write, for each shot, one query in each of these languages (ISO 639-1 codes: %s) in the words '
                 'an uploader of nature footage in that language would use; give every query its language code. '
                 'Return JSON {queries:[{shot_id:integer,lang:string,query:string}]}, with lang "en" for the English one. '
                 % ", ".join(languages)) if languages else ' Return JSON {queries:[{shot_id:integer,query:string}]}. '
    rows = api("flash", 'For each documentary shot below write ONE footage search query of 3-7 English words, run on YouTube, '
               'the Internet Archive, Wikimedia Commons and NASA, that '
               'finds real camera footage of the subject its narration names (for example "container ship engine '
               'room generator b-roll"). Use footage words such as b-roll, raw footage, aerial, onboard; never words '
               'that find interviews, news anchors or explainers.' + localized +
               'SHOTS:' + str(shots), folder / "queries.json", tokens=2000 + 600 * len(languages))["data"].get("queries") or []
    # (language, query) pairs, English first: only English runs on the
    # priority channels, whose titles are English.
    asked_by = {}
    for r in rows:
        if r.get("query"):
            pair = (str(r.get("lang") or "en").strip().lower(), str(r.get("query", "")).strip().lower())
            asked_by.setdefault(pair, set()).add(r.get("shot_id"))
    pairs = sorted((p for p in asked_by if p[0] == "en" or p[0] in languages), key=lambda p: p[0] != "en")
    queries = [q for _, q in pairs]
    event(out, "shot_source_search_started", shots=len(shots), queries=len(queries),
          profile=production["name"], languages=sorted({lang for lang, _ in pairs}))

    def lookup(item):
        index, (lang, query) = item
        if not languages:
            return sources.search(query, folder / f"query_{index:03}")["candidates"]
        if lang == "en":
            return sources.search(query, folder / f"query_{index:03}", channels=production.get("priority_channels") or (),
                                  sites=production.get("sites"), channel_take=production.get("channel_take", 5))["candidates"]
        return sources.search(query, folder / f"query_{index:03}_{lang}", sites=("youtube",),
                              limit=production.get("localized_take", 10))["candidates"]

    with ThreadPoolExecutor(max_workers=production.get("search_workers", 6)) as pool:
        found = list(pool.map(lookup, enumerate(pairs)))
    # A ".nonbbc" marker (sources.relax_channels) is not a fetched source.
    known = {p.name.split("_windows")[0].split(".")[0] for p in (out / "sources").glob("*") if p.suffix != ".nonbbc"}
    picked, seen = [], set()
    # The first unseen results of each query, round robin, so every
    # sentence gets its own footage before any one query gets more: two
    # per query by default, three for the wildlife profile.
    picked_for = {}
    for rank in range(production.get("per_query_take", 2)):
        for pair, results in zip(pairs, found):
            # A YouTube result without a duration is a live stream; the
            # archives often leave the duration out, and the probe reads it.
            fresh = [c for c in results if c.get("id") and c["id"] not in known and c["id"] not in seen
                     and (20 <= float(c.get("duration") or 0) <= 3600
                          or c.get("duration") is None and c.get("site", "youtube") != "youtube")]
            # fresh already leaves out what earlier ranks took, so its head
            # is the next unseen result; fresh[rank] skipped every second
            # one and gave a query with two fresh results only one source.
            if fresh and len(picked) < max_sources:
                seen.add(fresh[0]["id"]); picked.append(fresh[0])
                for sid in asked_by[pair]:
                    picked_for[str(sid)] = picked_for.get(str(sid), 0) + 1

    def fetch(candidate):
        set_context(out)
        url = candidate.get("url") or "https://www.youtube.com/watch?v=" + candidate["id"]
        try:
            meta = sources.probe_source(url, out)
            if float(meta.get("duration") or 0) <= 90:
                return sources.scene_shots(sources.download(url, out), out)
            files, payload = sources.fetch_source_windows(url, meta, out, count=sources.MAX_USES_PER_ORIGIN)
        except Exception as exc:
            event(out, "shot_source_unavailable", id=candidate["id"], error=type(exc).__name__)
            return []
        return [{"id": "%s_%03d" % (meta.get("id"), i), "kind": "VIDEO", "path": str(f),
                 "start": w["source_start"], "end": w["source_end"], "local_start": 0.0, "local_end": w["length_sec"],
                 "sha256": sha(f), "source_url": meta.get("url"), "source_title": meta.get("title"),
                 "rights": meta.get("rights"), "native_width": int(meta.get("width") or 0),
                 "native_height": int(meta.get("height") or 0), "source_start": w["source_start"],
                 "source_end": w["source_end"], "range_file": True}
                for i, (w, f) in enumerate(zip((payload or {}).get("windows") or [], files or []))]

    def fetch_and_fingerprint(candidate):
        # A source's windows are fingerprinted in the background as soon
        # as they land, so the footage grouping that follows the search
        # reads them from the cache.
        rows = fetch(candidate)
        footage.prefetch(rows)
        window_index.prefetch(rows)
        return rows

    with ThreadPoolExecutor(max_workers=8) as pool:
        windows = [row for rows in pool.map(fetch_and_fingerprint, picked) for row in rows]
    groups = [windows[i:i + 6] for i in range(0, len(windows), 6)]
    base = 900000 + int(digest(shots)[:4], 16) * 100
    with ThreadPoolExecutor(max_workers=10) as pool:
        classified = [a for group in pool.map(lambda g: sources.describe_group(g[1], base + g[0], out), enumerate(groups))
                      for a in group]
    assets = [a for a in classified if a.get("category") == "VIDEO" and a.get("usable")]
    save(manifest, {"status": "COMPLETE", "queries": queries, "sources": len(picked),
                    "windows": len(windows), "assets": assets})
    event(out, "shot_source_search_finished", queries=len(queries), sources=len(picked),
          windows=len(windows), admitted=len(assets))
    # Sentences no source was found for (the source cap not reached), and a
    # lone sentence whose sources gave no usable footage, are not searched again.
    barren = [s for s in failed_shots if len(picked) < max_sources and not picked_for.get(str(s["shot_id"]))]
    if len(failed_shots) == 1 and not assets:
        barren = list(failed_shots)
    if barren:
        with _INFLIGHT_LOCK:
            ledger = _empty_ledger(out)
            known = list(load(ledger).get("sentences") or []) if ledger.is_file() else []
            save(ledger, {"sentences": list(dict.fromkeys(known + [_sentence_key(s) for s in barren if _sentence_key(s)]))})
    return assets


def batch_identity(shots, out):
    """(identity, legacy identity) of a recovery batch for these shots.

    The legacy one is the older whole-file identity: a batch made under it
    is found under its own name while those files are unchanged.
    """
    from . import catalog_policy, code_identity
    identity = digest({"shots": shots, "version": RECOVERY_VERSION, "code": code_identity.module_hash("recovery.py"),
                       "source_policy": catalog_policy.policy(profiles.for_run(out))})
    legacy = digest({"shots": shots, "policy_sha256": sha(Path(__file__)), "source_policy_sha256": sha(Path(sources.__file__))})
    return identity, legacy


def recover_sources(failed_shots, out):
    """One40s local-cache recovery, at most12filters and one Flash classification."""
    started = time.monotonic()
    deadline = started + 90
    out = Path(out)
    set_context(out)
    shots = [{k: shot.get(k) for k in ("shot_id", "category", "start", "end", "narration", "story_plan", "reason", "problem")}
             for shot in failed_shots if shot.get("category") == "VIDEO"]
    if not shots:
        return []
    identity, legacy = batch_identity(shots, out)
    for key in (identity, legacy):
        manifest = out / "source_recovery" / key[:16] / "result.json"
        if manifest.exists():
            stored = load(manifest)
            if stored.get("identity") == key and stored.get("status") == "COMPLETE" and stored.get("assets"):
                return _admit(stored.get("assets", []), {a["id"]: a for a in stored.get("assets", [])})
    directory = out / "source_recovery" / identity[:16]
    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory / "result.json"
    event(out, "source_recovery_started", shots=[s["shot_id"] for s in shots], batch=str(directory))
    try:
        windows = []
        # A bounded recovery cannot discover/download long remote sources. Reuse
        # admitted local source bounds, preserving all provenance and final QA.
        for source in sorted((out/"sources").glob("*_shots.json")):
            if time.monotonic() >= deadline - 5: break
            meta_path = source.with_name(source.name.replace("_shots.json", ".json"))
            if not meta_path.is_file(): continue
            meta=load(meta_path);stream=next((s for s in meta.get("probe",{}).get("streams",[]) if s.get("codec_type")=="video"),{})
            stored=load(source)
            if stored.get("source_sha256")!=meta.get("sha256"): continue
            windows.extend({**row,"native_height":int(stream.get("height") or 0),"native_width":int(stream.get("width") or 0)} for row in stored.get("rows",[]))
        candidates = sources.shortlist(sorted((r for r in windows if int(r.get("native_height") or 0)>=1080
            and float(r.get("end",0))>float(r.get("start",0))), key=lambda r: r["id"]), 12)[:12]
        local_deadline=min(deadline-5,started+12)
        def inspect_window(row):
            set_context(out)
            folder=directory/"local_qc"/row["id"]
            folder.mkdir(parents=True,exist_ok=True)
            remaining=local_deadline-time.monotonic()
            if remaining<=0: return None
            a,b=float(row["start"]),float(row["end"]);duration=b-a
            board=folder/"contact.jpg"
            command=["ffmpeg","-hide_banner","-threads","1","-ss",str(a),"-t",str(duration),"-i",str(row["path"]),"-an","-filter_complex_threads","1","-filter_complex",f"[0:v]split[qc][board];[qc]scale=320:-1,freezedetect=n=-45dB:d=0.7[checked];[board]fps={3/duration},scale=384:-1,tile=3x1[contact]","-map","[checked]","-f","null","NUL","-map","[contact]","-frames:v","1","-y",str(board)]
            try:
                process=subprocess.run(command,capture_output=True,timeout=remaining)
                log=process.stderr.decode(errors="replace")
                durations=[float(x) for x in re.findall(r"freeze_duration:\s*([\d.]+)",log)]
                starts=[float(x) for x in re.findall(r"freeze_start:\s*([\d.]+)",log)]
                if len(starts)>len(durations): durations.append(max(0,duration-starts[-1]))
                frozen=sum(durations);ok=process.returncode==0 and board.is_file() and frozen<=max(.8,duration*.12)
                save(folder/"freeze_qc.json",{"status":"PASS" if ok else "FAIL","frozen_seconds":frozen,"command":command,"returncode":process.returncode,"deadline_seconds":40})
                return {**row,"recovery_board":str(board)} if ok else None
            except subprocess.TimeoutExpired:
                save(folder/"freeze_qc.json",{"status":"FAIL","reason":"local deadline; subprocess.run killed FFmpeg","command":command})
                return None
        # The window inspection is the one place in the pipeline that
        # runs ffmpeg outside the memory gate. It used to open one
        # process per candidate, twelve at once, and each one decoded
        # the source at full resolution before scaling it down. That
        # is a memory spike the gate cannot see, and a spike is what
        # takes the screen down on a busy desktop. Four at a time is
        # the most the machine can carry while the rest of the run
        # keeps working.
        with ThreadPoolExecutor(max_workers=max(1,min(4,len(candidates)))) as pool:
            windows=[r for r in pool.map(inspect_window,candidates) if r is not None]
        classified=[]
        if windows:
            boards={}
            folder=directory/"inventory"
            folder.mkdir(exist_ok=True)
            for row in windows:
                boards[row["id"]]=row["recovery_board"]
            evidence=[{k:r.get(k) for k in ("id","start","end","source_title")} for r in windows]
            receipt=folder/"flash.json"
            review=api("flash",'Inspect this ONE group of at most12 real candidate windows. Each attached board has three actual frames and the window ID. '
                'Classify every ID exactly once. VIDEO requires actual moving physical camera footage; reject slideshows, CGI, presenters, burned-in subtitles, wrong mechanics and unrelated filler. '
                'Logos, watermarks, LIVE or timestamp tags, news graphics, lower thirds and title cards are no reason to reject. '
                'Relevant physical demonstrations may illustrate the narrated mechanism with the visible label Illustrative live footage; original historical hardware and exact spoken measurements are not required. '
                'Return JSON {rows:[{id,category:VIDEO|REJECT,usable:boolean,description:string,keywords:[string],problems:[string]}]}. '
                f'FAILED SHOTS:{shots}\nWINDOWS:{evidence}',receipt,images=list(boards.values()),tokens=4200,
                timeout=max(.1,deadline-time.monotonic()-2),deadline=deadline-2,max_attempts_override=1,hedge_override=0)["data"]["rows"]
            byid={r["id"]:r for r in review if isinstance(r, dict) and "id" in r}
            classified=[{**row,**byid.get(row["id"], {"category": "VIDEO", "usable": True, "description": "Illustrative recovery candidate", "keywords": [], "problems": []}),
                         "sample_contact":boards[row["id"]],"classification_receipt":str(receipt),
                         "classification_sampling":"one grouped API round; three actual frames per window; locally freeze-checked"} for row in windows]
        assets = _admit(classified, {r["id"]: r for r in windows})
        if time.monotonic()>deadline: raise TimeoutError("Recovery40second global deadline exceeded")
        save(manifest, {"identity": identity, "status": "COMPLETE", "selected_sources": len({r.get("source_url") for r in windows}),"elapsed_seconds":round(time.monotonic()-started,3),"deadline_seconds":40,"api_classification_calls":int(bool(windows)),
             "classified_windows": len(windows), "assets": assets,
             "scope": "Three sampled real source frames per window; final shot still requires independent review"})
        event(out, "source_recovery_complete", admitted=len(assets), classified=len(windows))
        return assets
    except CancelledError:
        raise
    except Exception as exc:
        save(manifest, {"identity": identity, "status": "UNAVAILABLE", "error": type(exc).__name__,"elapsed_seconds":round(time.monotonic()-started,3),"deadline_seconds":40, "assets": []})
        event(out, "source_recovery_unavailable", error=type(exc).__name__)
        return []
