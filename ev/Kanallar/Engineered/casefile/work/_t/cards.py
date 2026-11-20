import sys; sys.path.insert(0,"..")
sys.path.insert(0,r"C:\Users\meteh\Kanallar\Engineered\casefile")
import cf_gfx as G
from cf_common import *
G.setscale(.5)
import json
p=json.load(open(r"C:\Users\meteh\Kanallar\Engineered\casefile\work\EP04_Greenfield_Iowa_2024\cf_plan.json",encoding="utf8"))
first={}
for c in p["cards"]: first.setdefault(c["kind"],c)
first["section"]=dict(kicker="PART II",title="FORTY-EIGHT MINUTES",tease="That isn't rain.")
first["memorial"]=dict(text=p["memorial"]["text"]); first["endcard"]={}
from PIL import Image
for k,c in first.items():
    spec={x:v for x,v in c.items() if x not in("rows","kind")}
    D=6.0
    draw,ev=G.CARDS[k](spec,D,100)
    for tt in (1.2,4.5):
        fr=(Image.new("RGBA",G.sq(),INK+(255,)) if k in G.DARK else G.topo_crop(100+tt).convert("RGBA")); draw(tt,fr)
        fr.convert("RGB").save(f"work/_t/{k}_{tt}.jpg",quality=85)
    print(k,ev)
