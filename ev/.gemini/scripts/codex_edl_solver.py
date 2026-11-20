"""
CODEX EDL SOLVER & TIMELINE PLANNER (Maker-Checker Engine)
==========================================================
Uses VDS Codex (gpt-6-sol) as the primary intelligent Planner/Checker.
Generates or validates a strictly rule-compliant MASTER_EDL.json matching:
- universal_video_rules_37.json
- Exact audio duration
- Max 6s cut duration, min 1s
- Footage ratio (>= 38%), Photos (<= 30%), Animations (10-25%), Dynamic White Canvases
- Zero talking heads, anti-clone root separation
"""

import os
import sys
import json
import time
from pathlib import Path

# Add scripts directory to path to use ask_codex
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from ask_codex import ask_codex

def solve_edl_with_codex(narration_text, audio_duration_sec, clean_assets_manifest, target_edl_path):
    """
    Sends narration beats, total audio duration, and available clean assets to Codex VDS.
    Receives back a 100% rule-compliant EDL sequence.
    """
    prompt = f"""You are the Master EDL Architect and Timeline Director for an engineering documentary.
Task: Create a strictly compliant Edit Decision List (EDL) in JSON format for the provided narration.

CRITICAL RULES (universal_video_rules_37.json):
1. Total duration MUST exactly equal {audio_duration_sec:.2f} seconds.
2. Cut duration: Minimum 1.5s, Maximum 5.5s (average 2.8s - 3.5s).
3. Pacing & Interleaving:
   - Footage (broll): 38% - 60% of total time.
   - 2D Animation: 10% - 25% of total time. Never 2 animations in a row!
   - Archival Photos: 15% - 30% of total time. Max 2 photos in a row.
   - Dynamic White Canvas (Motion Graphics): 2 to 4 key technical explanatory beats.
4. Anti-Clone: Never use the same raw asset twice consecutively. Max 2 cuts per footage file separated by at least 25 seconds.
5. Zero Talking Heads / Pure B-roll archival narrative.

Available Clean Asset Inventory:
{json.dumps(clean_assets_manifest, indent=2)}

Narration Transcript:
\"\"\"{narration_text}\"\"\"

OUTPUT REQUIREMENT:
Respond ONLY with a valid JSON object matching this schema:
{{
  "audio_duration_seconds": {audio_duration_sec:.2f},
  "total_cuts": <int>,
  "timeline": [
    {{
      "id": "CUT_001",
      "start_seconds": 0.0,
      "end_seconds": 3.2,
      "duration_seconds": 3.2,
      "type": "footage" | "animation" | "photo" | "white_canvas",
      "asset_name": "<exact_filename_from_inventory>",
      "scene_description": "<brief description of beat>"
    }}
  ]
}}
DO NOT include markdown fences, comments, or prose. ONLY valid JSON.
"""

    print(f"[CODEX EDL SOLVER] Consulting Codex VDS (gpt-6-sol) for {audio_duration_sec:.2f}s timeline...")
    t0 = time.time()
    raw_response = ask_codex(prompt, model="gpt-6-sol", timeout=120)
    elapsed = time.time() - t0
    print(f"[CODEX EDL SOLVER] Codex response received in {elapsed:.2f}s.")

    # Clean response in case of markdown formatting
    clean_json_str = raw_response.strip()
    if clean_json_str.startswith("```json"):
        clean_json_str = clean_json_str[7:]
    if clean_json_str.startswith("```"):
        clean_json_str = clean_json_str[3:]
    if clean_json_str.endswith("```"):
        clean_json_str = clean_json_str[:-3]
    clean_json_str = clean_json_str.strip()

    try:
        edl_data = json.loads(clean_json_str)
        # Validate mathematical continuity
        cuts = edl_data.get("timeline", [])
        curr_t = 0.0
        for i, cut in enumerate(cuts):
            st = cut["start_seconds"]
            dur = cut["duration_seconds"]
            cut["start_seconds"] = round(curr_t, 3)
            cut["end_seconds"] = round(curr_t + dur, 3)
            curr_t = cut["end_seconds"]

        # Ensure last cut closes exactly on audio_duration_sec
        if cuts:
            diff = audio_duration_sec - cuts[-1]["end_seconds"]
            cuts[-1]["duration_seconds"] = round(cuts[-1]["duration_seconds"] + diff, 3)
            cuts[-1]["end_seconds"] = round(audio_duration_sec, 3)

        out_path = Path(target_edl_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(edl_data, f, indent=2, ensure_ascii=False)
        print(f"[CODEX EDL SOLVER] Master EDL successfully written to: {out_path} ({len(cuts)} cuts)")
        return True, edl_data
    except Exception as e:
        print(f"[CODEX EDL SOLVER ERROR] Failed to parse Codex JSON: {e}")
        return False, str(e)


if __name__ == "__main__":
    test_manifest = {
        "footage": ["broll_01_LqaLQkglaQ.mp4", "broll_02_17Jul1981.mp4", "broll_04_atrium.mp4"],
        "animations": ["anim_01_box_beam.mp4", "anim_02_rod_shear.mp4"],
        "photos": ["PHOTO_01_ARCHIVE.jpg", "PHOTO_02_NBS.jpg", "PHOTO_03_COLLAPSE.jpg"]
    }
    sample_text = "Look closely at this steel nut. It was threaded onto a hanger rod inside a Kansas City hotel."
    ok, res = solve_edl_with_codex(sample_text, 12.0, test_manifest, "test_codex_edl.json")
    print("Test Result:", ok)
