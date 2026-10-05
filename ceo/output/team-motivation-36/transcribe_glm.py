#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 GLM 视觉模型逐字转录书页图片。用法: python3 transcribe_glm.py <img> [model]"""
import base64, json, os, sys, urllib.request

KEY = json.load(open(os.path.expanduser("~/.openclaw/config/glm.json")))["api_key"]
MODEL = sys.argv[2] if len(sys.argv) > 2 else "glm-4v-flash"
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

PROMPT = (
    "请把这张书页图片里的所有中文文字逐字转录出来。要求：\n"
    "1. 严格按页面阅读顺序（从上到下、从左到右）输出，保留标题、小标题、正文、案例、页码等所有可见文字。\n"
    "2. 一字不漏、不改写、不总结、不补充、不解释，原样输出。\n"
    "3. 段落之间用空行分隔；如果页面有分栏或独立文本框，请按视觉位置顺序输出。\n"
    "4. 只输出转录文字本身，不要任何前言后语。"
)

payload = {
    "model": MODEL,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64(sys.argv[1])}},
            {"type": "text", "text": PROMPT},
        ],
    }],
    "temperature": 0.01,
}
req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                             headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    print(out["choices"][0]["message"]["content"])
except urllib.error.HTTPError as e:
    print("HTTPError", e.code, e.read().decode()[:500])
except Exception as e:
    print("ERR", type(e).__name__, e)
