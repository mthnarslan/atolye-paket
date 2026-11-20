import sys, json, os
os.environ["DOCUMENTARY_YT_COOKIES_BROWSER"]="firefox"
sys.path.insert(0, r"C:\Users\meteh\.gemini\scripts")
from documentary_materials import sources
out=r"C:\Users\meteh\CodexOutputs\EP03_Nepal_Tibet_Glacier_Flood_2026\03_materials"
seen={}
for q in ["seismograph recording earthquake","seismometer drum needle earthquake b-roll","seismic monitoring station screens earthquake","USGS seismograph","seismograph needle drawing paper drum","earthquake monitoring center seismic waves screen"]:
    try:
        r=sources.search(q,out,limit=15)
    except Exception as e:
        print(q,"ERR",e); continue
    for c in (r if isinstance(r,list) else r.get("candidates",r.get("results",[]))):
        i=c.get("id")
        if i in seen: continue
        seen[i]=c
        print(q[:20],"|",i,"|",c.get("title","")[:70],"|",c.get("duration"),"|",c.get("site"),c.get("width"),c.get("height"))
