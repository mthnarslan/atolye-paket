# UserPromptSubmit: warn once if the 1h prompt cache has expired and the context is big.
# Costs no API calls. Disable: set env CACHEWARN_OFF=1 or remove the hook from settings.json.
import json,sys,os,datetime as dt,time
try:
    d=json.load(sys.stdin); tp=d.get('transcript_path'); sid=d.get('session_id','')
    if os.environ.get('CACHEWARN_OFF') or not tp or not os.path.exists(tp): sys.exit(0)
    last=None;ctx=0
    with open(tp,'rb') as f:
        f.seek(max(0,os.path.getsize(tp)-400000))
        for l in f.read().decode('utf8','ignore').splitlines():
            if '"usage"' not in l: continue
            try:j=json.loads(l)
            except: continue
            if j.get('type')!='assistant' or j.get('isSidechain'): continue
            u=j['message'].get('usage') or {}
            c=u.get('cache_creation_input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('input_tokens',0)
            if c: ctx=c; last=dt.datetime.fromisoformat(j['timestamp'].replace('Z','+00:00')).timestamp()
    if not last: sys.exit(0)
    gap=time.time()-last
    if gap<3500 or ctx<120000: sys.exit(0)
    flag=os.path.join(os.path.dirname(__file__),'.cachewarn_seen'); key=f'{sid}:{int(last)}'
    seen=open(flag).read().split() if os.path.exists(flag) else []
    if key in seen: sys.exit(0)
    open(flag,'w').write('\n'.join((seen+[key])[-50:]))
    print(json.dumps({"decision":"block","reason":f"Önbellek doldu ({gap/3600:.1f} saat ara). Şimdi gönderirsen ~{ctx//1000}k token 2 kat fiyattan yeniden yazılır. Ucuzu: önce /compact, ya da yeni oturum (DURUM.md durumu geri yükler). Yine de devam için aynı mesajı tekrar gönder."}))
except Exception as e:
    if os.environ.get("CW_DEBUG"): raise
