#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中秋礼单表审计（只读）：拉全表 -> 统计重复序号/重名/未复核，供 dreaming 取证"""
import json, urllib.request, collections, os

CFG = os.path.expanduser("~/.openclaw/openclaw.json")
cfg = json.load(open(CFG))

def find_app(cfg):
    # 深度遍历找 appId/appSecret
    out = {}
    def walk(o):
        if isinstance(o, dict):
            if "appId" in o and "appSecret" in o:
                out.setdefault("appId", o["appId"])
                out.setdefault("appSecret", o["appSecret"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(cfg)
    return out

app = find_app(cfg)
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=json.dumps({"app_id": app["appId"], "app_secret": app["appSecret"]}).encode(),
    headers={"Content-Type": "application/json"})
tok = json.load(urllib.request.urlopen(req))["tenant_access_token"]

APP = "Kef2bE601agEKGsCxeGc8n0HnId"
TBL = "tblz46KG5vphhXVx"
recs = []
page = ""
while True:
    url = (f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP}/tables/{TBL}/records"
           f"?page_size=500&page_token={page}")
    r = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    d = json.load(urllib.request.urlopen(r))
    data = d.get("data", {})
    recs += data.get("items", [])
    if not data.get("has_more"):
        break
    page = data.get("page_token", "")

print("TOTAL_RECORDS", len(recs))

def g(f, k):
    v = f.get(k)
    if isinstance(v, list):
        return "".join(x.get("text", "") for x in v if isinstance(x, dict))
    return v if v is not None else ""

names = collections.Counter()
seqs = collections.Counter()
for r in recs:
    f = r.get("fields", {})
    names[g(f, "名字").strip()] += 1
    s = str(g(f, "序号")).strip()
    if s:
        seqs[s] += 1

print("\n== 名字重复（>1）==")
for n, c in sorted(names.items(), key=lambda x: -x[1]):
    if c > 1:
        print(f"  {n} x{c}")

print("\n== 序号重复（>1）==")
dup = {k: v for k, v in seqs.items() if v > 1}
print("  重复序号个数:", len(dup))
for k, v in sorted(dup.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
    print(f"  序号{k} x{v}")

print("\n== 序号数值范围 ==")
nums = sorted(int(k) for k in seqs if k.isdigit())
print("  min", nums[0], "max", nums[-1], "distinct", len(nums))
missing = [i for i in range(nums[0], nums[-1] + 1) if i not in set(nums)]
print("  缺失序号:", missing)

print("\n== 今日新增 7 人定位 ==")
for target in ["Zoey", "zoe", "可可", "冉总", "黄总", "Erica", "莹莹宝", "Jessie", "费老", "哟哟", "Yoyo"]:
    hits = []
    for r in recs:
        f = r.get("fields", {})
        if g(f, "名字").strip() == target:
            hits.append((g(f, "序号"), g(f, "公司"), g(f, "收件信息")[:40], g(f, "地址复核")))
    if hits:
        for h in hits:
            print(f"  {target}: 序号{h[0]} | 公司={h[1]} | {h[2]} | 复核={h[3]}")
    else:
        print(f"  {target}: 未找到")

print("\n== 地址复核未打勾 ==")
n_un = 0
for r in recs:
    f = r.get("fields", {})
    if not f.get("地址复核"):
        n_un += 1
        print(f"  序号{g(f,'序号')} {g(f,'名字')} | {g(f,'收件信息')[:50]}")
print("  未复核合计:", n_un)
