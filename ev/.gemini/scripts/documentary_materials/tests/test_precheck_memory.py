import json
from pathlib import Path
from documentary_materials import runner

def A(i,o,s,e,cat="VIDEO",**k):return {"id":i,"category":cat,"origin_id":o,"start":s,"end":e,**k}

def test_window_overlap_and_filter(tmp_path, monkeypatch):
    monkeypatch.setattr(runner,"_origin_id",lambda a:a.get("origin_id"))
    bad=A("x_000","youtube:X",10,30)
    runner._remember_rejected_window(tmp_path,5,bad)
    assets=[A("x_001","youtube:X",12,28),A("x_002","youtube:X",40,60),A("y_000","youtube:Y",10,30),A("p","youtube:X",10,30,cat="PHOTO")]
    got=runner._with_window_memory(tmp_path,{"shot_id":7},assets,("a",))
    assert set(got)=={"a","x_001"}          # same origin+window only, neighbour within 2
    assert set(runner._with_window_memory(tmp_path,{"shot_id":8},assets,()))==set()   # beyond radius 2

def test_multi_source_not_remembered(tmp_path, monkeypatch):
    monkeypatch.setattr(runner,"_origin_id",lambda a:a.get("origin_id"))
    multi={"segments":[A("a","youtube:A",0,5),A("b","youtube:B",0,5)],"category":"VIDEO"}
    runner._remember_rejected_window(tmp_path,3,multi)
    assert runner._remembered_windows(tmp_path,3)==[]
    assert runner._remember_rejected_origins(tmp_path,3,["side bars"],multi["segments"])==[]
    assert runner._remember_rejected_origins(tmp_path,3,["side bars"],[A("a","youtube:A",0,5)])==["youtube:A"]

def test_after_reject_only_flash_fail_remembers_window(tmp_path, monkeypatch):
    monkeypatch.setattr(runner,"_origin_id",lambda a:a.get("origin_id"))
    a=A("x_000","youtube:X",10,30)
    runner._after_reject(tmp_path,{"shot_id":4},{"issues":["wrong subject"]},a)       # GPT, content: nothing
    assert runner._remembered_windows(tmp_path,4)==[]
    runner._after_reject(tmp_path,{"shot_id":4},{"issues":["wrong subject"],"precheck":"FLASH_FAIL"},a)
    assert len(runner._remembered_windows(tmp_path,4))==1

def test_off_switch(tmp_path, monkeypatch):
    monkeypatch.setattr(runner,"_origin_id",lambda a:a.get("origin_id"))
    monkeypatch.setattr(runner,"PRECHECK_MEMORY",False)
    runner._remember_rejected_window(tmp_path,5,A("x_000","youtube:X",10,30))
    assert runner._remembered_windows(tmp_path,5)==[]
    assert runner._with_window_memory(tmp_path,{"shot_id":5},[A("x_000","youtube:X",10,30)],("q",))==("q",)
