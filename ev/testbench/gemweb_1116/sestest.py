import base64, json, urllib.request, time
b = base64.b64encode(open("C:/Users/meteh/ortak-site/public/nasil/ses/s003_en.mp3","rb").read()).decode()
body = {"model":"gemini-4-hydrogen","reasoning_effort":"high","messages":[{"role":"user","content":[
 {"type":"text","text":"Transcribe this audio exactly."},{"type":"input_audio","input_audio":{"data":b,"format":"mp3"}}]}]}
t=time.time(); r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8790/v1/chat/completions", json.dumps(body).encode(), {"Content-Type":"application/json"}), timeout=300)
print(round(time.time()-t), json.load(r)["choices"][0]["message"]["content"][:200])
