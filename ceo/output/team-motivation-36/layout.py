import json, os, sys, urllib.request, base64
KEY = json.load(open(os.path.expanduser("~/.openclaw/config/glm.json")))["api_key"]
p=sys.argv[1]
b=base64.b64encode(open(p,'rb').read()).decode()
payload={"model":sys.argv[2] if len(sys.argv)>2 else "glm-4v-flash","messages":[{"role":"user","content":[
{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+b}},
{"type":"text","text":sys.argv[3]}]}],"temperature":0.01}
req=urllib.request.Request("https://open.bigmodel.cn/api/paas/v4/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
print(json.loads(urllib.request.urlopen(req,timeout=120).read().decode())["choices"][0]["message"]["content"])
