"""Re-audit a film's existing voice and repair only the chunks the judge flags (cached chunks are reused,
only rewritten ones are synthesised, master/manifest/hashes rebuilt). Usage: redo_voice.py <input folder>"""
import os, sys
os.environ.setdefault("DOCUMENTARY_VOICE_ENGINE", "pocket")
sys.path.insert(0, r"C:\Users\meteh\.gemini\scripts")
import documentary_voice_engine as engine, documentary_voice_audit as auditor, documentary_voice_repair as repair
manifest, audit = repair.run_with_repair(engine, auditor, sys.argv[1], lambda m: print(m, flush=True))
print(audit.get("verdict"), audit.get("next_step_allowed"), audit.get("repair_rounds"))
sys.exit(0 if audit.get("next_step_allowed") else 1)
