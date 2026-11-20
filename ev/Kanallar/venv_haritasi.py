import json, os, subprocess, sys, time
from pathlib import Path

OUT = Path(r"C:\Users\meteh\Kanallar\venv_haritasi.json")
ROOT = Path(r"C:\Users\meteh")

def candidates():
    out = {Path(sys.executable)}
    try:
        p = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=60)
        for line in p.stdout.splitlines():
            if ":\\" in line:
                out.add(Path(line.split()[-1]))
    except Exception:
        pass
    for base, dirs, files in os.walk(ROOT):
        rel = Path(base).relative_to(ROOT)
        if len(rel.parts) >= 4:
            dirs[:] = []
        else:
            dirs[:] = [d for d in dirs if d != "node_modules"]
        if "python.exe" in files and (".venv" in rel.parts or "venv" in rel.parts):
            out.add(Path(base) / "python.exe")
    return sorted(str(p) for p in out if p.is_file())

def inspect(py):
    t0=time.time()
    try:
        r=subprocess.run([py,"-m","pip","list","--format=json"],capture_output=True,text=True,timeout=60)
        rows=json.loads(r.stdout); o={}
        aliases={'faster-whisper':'faster_whisper','scikit-learn':'sklearn','scikit-image':'skimage','opencv-python':'cv2','pillow':'PIL','sentence-transformers':'sentence_transformers'}
        for row in rows:
            n=row.get('name',''); key=n.lower().replace('-','_')
            o.setdefault(key,[]).append(n)
            if n.lower() in aliases: o.setdefault(aliases[n.lower()].lower(),[]).append(n)
        return o, round(time.time()-t0,3)
    except Exception as e:
        return {}, round(time.time()-t0,3)

allmap={}; timings=[]
for py in candidates():
    m, sec=inspect(py); timings.append([py,sec,len(m)])
    for k in m:
        allmap.setdefault(k,[]).append(py)
OUT.write_text(json.dumps(allmap, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'interpreters':len(timings),'mapped_modules':len(allmap),'timings':timings}, ensure_ascii=False))
