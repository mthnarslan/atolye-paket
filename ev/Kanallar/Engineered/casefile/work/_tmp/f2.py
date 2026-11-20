import sys, json, os
os.environ["DOCUMENTARY_YT_COOKIES_BROWSER"]="firefox"
sys.path.insert(0, r"C:\Users\meteh\.gemini\scripts")
from documentary_materials import sources
out=r"C:\Users\meteh\CodexOutputs\EP03_Nepal_Tibet_Glacier_Flood_2026\03_materials"
for i,d in [("Gbd1FcuLJLQ",65),("gaAGnemUN7Q",21),("rEk_NPjDawU",78),("BzZhspiyg2I",91),("zgZrFIDMhyI",111),("Yaa9-bTeIso",41)]:
    meta={"id":i,"duration":d,"title":i,"site":None}
    try:
        w,m=sources.fetch_source_windows("https://www.youtube.com/watch?v="+i,meta,out,count=1)
        print(i,w,json.dumps(m)[:400])
    except Exception as e: print(i,"ERR",e)
