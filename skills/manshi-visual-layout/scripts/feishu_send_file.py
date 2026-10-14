#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用飞书 API 发真实文件（message 工具传 PNG 会被降级成 image 消息）。
用法: python3 feishu_send_file.py <abs_path> [open_id]
"""
import json, os, subprocess, sys, urllib.request

CFG = "/Users/yifansmacmini/.openclaw/openclaw.json"
DEFAULT_OPEN_ID = "ou_c4249d713be906d36ef8607efab6506f"


def token():
    c = json.load(open(CFG))["channels"]["feishu"]
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": c["appId"], "app_secret": c["appSecret"]}).encode(),
        headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))["tenant_access_token"]


def upload(path, tok):
    out = subprocess.run(["curl", "-s", "-X", "POST",
                          "https://open.feishu.cn/open-apis/im/v1/files",
                          "-H", f"Authorization: Bearer {tok}",
                          "-F", "file_type=stream",
                          "-F", f"file_name={os.path.basename(path)}",
                          "-F", f"file=@{path}"], capture_output=True, text=True)
    r = json.loads(out.stdout)
    if r.get("code") != 0:
        raise RuntimeError(r)
    return r["data"]["file_key"]


def send_file(path, open_id=DEFAULT_OPEN_ID):
    tok = token()
    key = upload(path, tok)
    body = json.dumps({"receive_id": open_id, "msg_type": "file",
                       "content": json.dumps({"file_key": key})}).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
        data=body, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req))
    print("sent:", r.get("code"), r.get("data", {}).get("message_id"))


if __name__ == "__main__":
    send_file(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OPEN_ID)
