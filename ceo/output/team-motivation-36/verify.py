#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys, urllib.request, base64

KEY = json.load(open(os.path.expanduser("~/.openclaw/config/glm.json")))["api_key"]

def ask(p, q, model="glm-4.5v"):
    b = base64.b64encode(open(p, "rb").read()).decode()
    payload = {"model": model, "messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b}},
        {"type": "text", "text": q}]}], "temperature": 0.01}
    req = urllib.request.Request("https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=150).read().decode())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "ERR %s" % e

base = "/Users/yifansmacmini/.openclaw/media/inbound/"
Q1 = "这张书页照片顶部的页眉文字和页码分别是什么？如果看不到页眉请回答“无页眉”。只回答页眉和页码，不要其他内容。"
Q2 = "这张书页里是否出现“直言不讳”这四个字？请把包含它的那句话原文照抄出来。"
Q3 = "这张书页里是否有“甚至更长的时间”这样的表述？请把包含“甚至更”的那句原文完整照抄出来。"

cases = [
    ("img15(15.md)", "b587860c-51b2-4d78-ab58-70b29a51899d.jpg", Q1),
    ("img18(18.md)", "f71a0428-b88b-4be3-a731-c1ea16fed960.jpg", Q1),
    ("img22(22.md)", "cc7af24f-77e1-4dd0-8cca-b6a286aac524.jpg", Q1),
    ("img24(24.md)", "c6a83ded-9e70-411d-af52-4c07e1b8ccf7.jpg", Q2),
    ("img20(20.md)", "683c2908-6a4c-4070-b2b0-db9aa3ac2ac1.jpg", Q3),
]
for name, p, q in cases:
    print("=== " + name + " ===")
    print(ask(base + p, q))
    print()
