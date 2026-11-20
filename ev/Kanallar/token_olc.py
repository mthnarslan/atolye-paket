"""Token olcumu (tum sohbetler): python C:/Users/meteh/Kanallar/token_olc.py <gun>  orn 1 ya da 0.5.
Goreli maliyet (API fiyat orani; limit formulu degil) rol/model ve okuma/yazma/cikti; ana baglam; zincir orani.
Taban 11-19 (3 gun): ana Opus %79 (okuma %50, yazma %16, cikti %14), Sonnet alt %14, Opus alt %6, ort ana baglam 127k, zincir %45."""
import glob,json,os,sys,collections as C,datetime as D,statistics as st
sys.stdout.reconfigure(encoding="utf-8")
gun=float(sys.argv[1]); t0=(D.datetime.now(D.timezone.utc)-D.timedelta(days=gun)).isoformat()[:19]
P={"opus":(5,6.25,.5,25),"sonnet":(3,3.75,.3,15),"haiku":(1,1.25,.1,5),"fable":(15,18.75,1.5,75)}
B=C.Counter(); ilk=[]; ctxs=C.defaultdict(list); seen=set(); n=C.Counter(); cw5=cw1=0
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/**/*.jsonl"),recursive=True):
    if os.path.getmtime(f)<D.datetime.now().timestamp()-gun*86400: continue
    sub="subagents" in f; first=True
    for l in open(f,encoding="utf-8",errors="replace"):
        try:o=json.loads(l)
        except:continue
        if o.get("type")!="assistant": continue
        m=o.get("message") or {}; u=m.get("usage") or {}
        if not u or (f,m.get("id")) in seen: continue
        seen.add((f,m.get("id")))
        if o.get("timestamp","")[:19]<t0: first=False; continue
        k=next((x for x in P if x in m.get("model","")),None)
        if not k: continue
        p=P[k]; r=("alt:" if sub else "ana:")+k
        ci,cc,cr,co=u.get("input_tokens",0),u.get("cache_creation_input_tokens",0),u.get("cache_read_input_tokens",0),u.get("output_tokens",0)
        cch=u.get("cache_creation") or {}; cw5+=cch.get("ephemeral_5m_input_tokens",0); cw1+=cch.get("ephemeral_1h_input_tokens",0)
        B[r+" okuma"]+=cr*p[2]/1e6; B[r+" yazma"]+=cc*p[1]/1e6; B[r+" cikti"]+=co*p[3]/1e6; B[r+" girdi"]+=ci*p[0]/1e6
        n[r]+=1; ctxs[r].append(cr+cc+ci)
        if first and not sub: ilk.append(cr+cc+ci)
        first=False
T=sum(B.values()); print(f"son {gun} gun goreli toplam ${T:.0f}; cagri {dict(n)}")
for k,v in B.most_common(12): print(f"  %{100*v/T:5.1f} {k}")
for r,v in ctxs.items(): print(f"  {r}: ort baglam {st.mean(v)/1000:.0f}k, medyan {st.median(v)/1000:.0f}k")
if ilk: print(f"  yeni ana oturum ilk cagri baglami medyan {st.median(ilk)/1000:.0f}k (n={len(ilk)})")
print(f"  cache yazma 5dk {cw5/1e6:.0f}M, 1sa {cw1/1e6:.0f}M")
# --- zincir olcumu: ust uste tek okuma/kabuk adimi (her biri tum baglami yeniden okutur) ---
calls=zincir=0
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    try:
        if os.path.getmtime(f)<D.datetime.now().timestamp()-gun*86400: continue
    except OSError: continue
    msgs={}; order=[]
    for l in open(f,encoding="utf-8",errors="replace"):
        try:o=json.loads(l)
        except:continue
        m=o.get("message") or {}
        if o.get("type")!="assistant" or "opus" not in m.get("model","") or o.get("timestamp","")[:19]<t0: continue
        i=m.get("id")
        if i not in msgs: msgs[i]=[]; order.append(i)
        msgs[i]+=[b.get("name") for b in m.get("content") or [] if isinstance(b,dict) and b.get("type")=="tool_use"]
    prev=None
    for i in order:
        calls+=1; x=msgs[i]; ok=len(x)==1 and x[0] in ("Read","Grep","Glob","Bash","PowerShell")
        if ok and prev: zincir+=1
        prev=ok
if calls: print(f"  ana opus cagri {calls}, ust uste tek okuma zinciri %{100*zincir/calls:.0f} (taban 11-19: %45)")
