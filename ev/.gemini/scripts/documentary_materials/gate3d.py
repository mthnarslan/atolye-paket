"""Pre-render 3D gate (testbench, not in prod). Pure Python, <1 ms per shot.

runner._fallback_mesh_spec picks a Hyatt-walkway / threaded-rod / bracing template by loose
keywords ("fall", "floor", "debris", "collapse", "strip"). On a film that is not about those
structures the template is a wrong-subject scene by construction (EP03: 7 of 7 rendered, 7 of 7
GPT-rejected). The gate only REFUSES early; a non-refused scene still goes to render + GPT.
"""
import re
_FALLBACK_CAPTIONS = ("Threaded Hanger Rod", "4th and 2nd Floor", "Lateral Bracing", "Qualitative 3D Structural")
_OWN = re.compile(r"hyatt|walkway|atrium|hanger|threaded|\bnuts?\b|washer|bolt|\brods?\b|bracing|brace|connection|girder|beam", re.I)

def is_fallback(spec):
    cap = (spec or {}).get("caption") or ""
    return any(cap.startswith(c) for c in _FALLBACK_CAPTIONS)

def misfit(shot, spec):
    """True when spec is a canned fallback template and the sentence is not about that structure."""
    if not is_fallback(spec):
        return False
    text = " ".join(str(shot.get(k) or "") for k in ("narration", "narrative_beat", "full_scene_narration"))
    return not _OWN.search(text)

REASON = "The only 3D scene available is a canned structural template that does not show this sentence; pick another medium."
