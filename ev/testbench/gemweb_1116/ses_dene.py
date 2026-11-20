import base64,json,sys,time,requests
f,fmt=sys.argv[1],sys.argv[2]
b=base64.b64encode(open(f,'rb').read()).decode()
q="Transcribe exactly what is spoken in the attached audio file. If you cannot hear or open any audio, reply only CANNOT."
t=time.time()
r=requests.post("http://127.0.0.1:8790/v1/chat/completions",json={"model":"gemini-4-hydrogen","reasoning_effort":"low","messages":[{"role":"user","content":[{"type":"text","text":q},{"type":"input_audio","input_audio":{"data":b,"format":fmt}}]}]},timeout=400)
j=r.json(); print(r.status_code, round(time.time()-t,1), j.get("hesap"), json.dumps(j.get("choices",[{}])[0].get("message",{}).get("content") or j, ensure_ascii=False)[:400])
