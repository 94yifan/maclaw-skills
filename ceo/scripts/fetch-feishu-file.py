#!/usr/bin/env python3
import json, urllib.request, urllib.parse, os, sys

CFG = "/Users/yifansmacmini/.openclaw/openclaw.json"
MSG_ID = sys.argv[1] if len(sys.argv) > 1 else "om_x100b657bb073f4acb4ad8960ef678a4"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "/Users/yifansmacmini/.openclaw/workspace/ceo/meetings"

cfg = json.load(open(CFG))
f = cfg["channels"]["feishu"]
app_id = f["appId"]; app_secret = f["appSecret"]

def post(url, data, headers=None):
    body = json.dumps(data).encode()
    h = {"Content-Type": "application/json; charset=utf-8"}
    if headers: h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())

def get(url, headers=None, raw=False):
    req = urllib.request.Request(url, headers=headers or {})
    r = urllib.request.urlopen(req, timeout=120)
    data = r.read()
    return data if raw else json.loads(data.decode())

# 1. tenant token
tok = post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
           {"app_id": app_id, "app_secret": app_secret})
print("token:", tok.get("code"), tok.get("msg"))
tat = tok["tenant_access_token"]
H = {"Authorization": f"Bearer {tat}"}

# 2. message
m = get(f"https://open.feishu.cn/open-apis/im/v1/messages/{MSG_ID}", H)
print("msg code:", m.get("code"), m.get("msg"))
items = m.get("data", {}).get("items", [])
if not items:
    print(json.dumps(m, ensure_ascii=False)[:800]); sys.exit(1)
it = items[0]
print("msg_type:", it.get("msg_type"))
content = json.loads(it["body"]["content"])
print("content keys:", list(content.keys()))
file_key = content.get("file_key") or content.get("image_key")
file_name = content.get("file_name", "download.bin")
print("file_name:", file_name, "file_key:", (file_key or "")[:12], "...")

# 3. download resource
os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, file_name)
url = f"https://open.feishu.cn/open-apis/im/v1/messages/{MSG_ID}/resources/{file_key}?type=file"
raw = get(url, H, raw=True)
open(out, "wb").write(raw)
print("saved:", out, os.path.getsize(out), "bytes")
