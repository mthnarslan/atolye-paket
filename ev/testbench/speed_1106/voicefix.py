"""Re-voice only the chunks the audit flagged as off-voice or with dropped/misread words (kind voice|text), with a new seed, same text.

python voicefix.py <CodexOutputs film dir> [--apply]

Uses the pipeline's own repair state file (voice_repair_state.json -> validated_overrides in
run_step1): the chunk text stays the approved text, only its seed changes. With --apply it also
moves master_voiceover.wav aside so the next stage-1 run regenerates (all other chunks come from
the chunk cache) and re-audits.
"""
import json, sys, shutil, time
from pathlib import Path

sys.path.insert(0, r"C:\Users\meteh\.gemini\scripts")
import documentary_voice_engine as eng  # read-only import

out = Path(sys.argv[1])
apply = "--apply" in sys.argv
man = json.loads((out / "voice_manifest.json").read_text(encoding="utf-8"))
aud = json.loads((out / "voice_audit.json").read_text(encoding="utf-8"))
issues = [i for i in (aud.get("gemini_audio") or {}).get("issues", []) if i.get("kind") in ("voice", "text")]  # text: Pocket dropped/misread words -> same text, new seed
tl = man["chunk_timeline"]
base = list(man.get("approved_chunks") or man["chunks"])
ident = eng.repair_identity(base, man["reference_audio"], man.get("language", "en"))
statep = out / "voice_repair_state.json"
state = json.loads(statep.read_text(encoding="utf-8")) if statep.exists() else {}
if state.get("identity") != ident:
    state = {"version": 1, "identity": ident, "overrides": {}}
ov = state.setdefault("overrides", {})
changed = 0
for i in issues:
    s, e = i["start_sec"], i["end_sec"]
    for c in tl:
        if c["start_sec"] < e and c["end_sec"] > s and min(c["end_sec"], e) - max(c["start_sec"], s) >= 0.3:
            k = str(c["id"])
            old = ov.get(k, {}).get("seed", 42)
            ov[k] = {"text": base[c["id"]], "seed": (old + 53) % 10001}
            changed += 1
            print(f"chunk {k} [{c['start_sec']:.1f}-{c['end_sec']:.1f}] seed {old}->{ov[k]['seed']}: {base[c['id']][:70]}")
if apply and changed:
    statep.write_text(json.dumps(state, indent=2), encoding="utf-8")
    keep = out / f"_offvoice_{time.strftime('%H%M%S')}"
    keep.mkdir()
    for n in ("master_voiceover.wav", "voice_audit.json"):
        if (out / n).exists():
            shutil.move(str(out / n), str(keep / n))
    print("applied; master moved to", keep)
