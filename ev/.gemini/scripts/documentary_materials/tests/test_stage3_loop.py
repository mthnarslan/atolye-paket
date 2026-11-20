import json, sys, tempfile
from pathlib import Path
from documentary_materials import planning, runner

def _plan():
    shots=[]
    for i in range(1,7):
        shots.append({"shot_id":i,"scene_id":i,"category":"3D" if i==5 else "VIDEO","narration":f"line {i}","duration_sec":4.0,
                      "frame_start":(i-1)*100,"frame_end":i*100,"timeline_start_sec":10.0*i,"timeline_end_sec":10.0*i+4.0,"story_plan":{"scene_id":i,"shot_id":i,"category":"VIDEO","visual_goal":"g","context":"c","transition":"t"}})
    return {"shots":shots,"targets":{"VIDEO":40,"PHOTO":10,"3D":10,"CARD":10,"ANIM":10,"MOTION":20},"identity":"x"}

def test_escalation_ladder_and_history():
    out=Path(tempfile.mkdtemp())
    plan=_plan()
    p2,ch=planning.escalate_unresolved(plan,out,[{"shot_id":5,"status":"REVIEW_REQUIRED"},{"shot_id":1,"status":"REVIEW_REQUIRED"}])
    assert ch==[5]                       # shot 1 starts at 10 s (< hook limit 30 s? 10<30 -> hook, untouched)
    assert [s for s in p2["shots"] if s["shot_id"]==5][0]["category"]=="MOTION"
    assert p2["failed_categories"]["5"]==["3D"]
    # a second failure moves on: MOTION failed -> ANIM
    p3,ch=planning.escalate_unresolved(p2,out,[{"shot_id":5,"status":"REVIEW_REQUIRED"}])
    c=[s for s in p3["shots"] if s["shot_id"]==5][0]["category"]
    assert ch==[5] and c in ("ANIM","PHOTO") and set(p3["failed_categories"]["5"])>={"3D","MOTION"}
    assert (out/"material_plan.json").exists()

def test_escalation_never_returns_failed_medium():
    out=Path(tempfile.mkdtemp()); plan=_plan(); cur=plan
    seen=set()
    for _ in range(8):
        cur,ch=planning.escalate_unresolved(cur,out,[{"shot_id":4,"status":"NO_MATCH"}])
        if not ch:break
        cat=[s for s in cur["shots"] if s["shot_id"]==4][0]["category"]
        assert cat not in seen; seen.add(cat)
    assert len(seen)>=3

def test_rejection_memory_class_and_neighbours():
    out=Path(tempfile.mkdtemp())
    a={"id":"abc_000","category":"VIDEO","origin":"youtube:abc"}
    got=runner._remember_rejected_origins(out,10,["Portrait video with black side bars"],[a])
    assert got==[runner._origin_id(a)] and got
    # window-specific reason is not remembered
    assert runner._remember_rejected_origins(out,11,["shows a different subject"],[a])==[]
    assert runner._remembered_origins(out,12)=={runner._origin_id(a)}      # neighbour within radius
    assert runner._remembered_origins(out,8)=={runner._origin_id(a)}
    assert runner._remembered_origins(out,13)==set()                       # outside radius 2
