#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中秋礼单表直连脚本：create / update / get / delete / find / findmany。
用法:
  python3 rec_api.py create '{"名字":"x","收件信息":"..."}'
  python3 rec_api.py update <record_id> '{"地址复核":true}'
  python3 rec_api.py get <record_id>
  python3 rec_api.py find <关键字>              # 在名字/收件信息/公司里模糊查
  python3 rec_api.py findmany <kw1> [kw2 ...]  # 一次全表遍历匹配多个关键字（提速）
"""
import json, sys, urllib.request, urllib.parse, os, time, re

CFG = os.path.expanduser("~/.openclaw/openclaw.json")
cfg = json.load(open(CFG))


def find_app(o, out=None):
    if out is None:
        out = {}
    if isinstance(o, dict):
        if "appId" in o and "appSecret" in o:
            out.setdefault("appId", o["appId"])
            out.setdefault("appSecret", o["appSecret"])
        for v in o.values():
            find_app(v, out)
    elif isinstance(o, list):
        for v in o:
            find_app(v, out)
    return out


APP = "Kef2bE601agEKGsCxeGc8n0HnId"
TBL = "tblz46KG5vphhXVx"
BASE = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP}/tables/{TBL}/records"


TOK_CACHE = "/tmp/.cfo_feishu_tok.json"


def token():
    """tenant_access_token，带本地缓存（有效期 2h，提前 120s 失效重取）。
    缓存目的是避免每次 rec_api 调用都重取 token（9/16 find 串行超 10s 的根因之一）。"""
    try:
        c = json.load(open(TOK_CACHE))
        if float(c.get("expires_at", 0)) > time.time() + 60 and c.get("token"):
            return c["token"]
    except Exception:
        pass
    a = find_app(cfg)
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": a["appId"], "app_secret": a["appSecret"]}).encode(),
        headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req))
    tok = r["tenant_access_token"]
    try:
        json.dump({"token": tok,
                   "expires_at": time.time() + int(r.get("expire", 7200)) - 120},
                  open(TOK_CACHE, "w"))
    except Exception:
        pass
    return tok


def call(method, url, tok, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {tok}",
                                          "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode(errors="replace")}


def g(f, k):
    v = f.get(k)
    if isinstance(v, list):
        return "".join(x.get("text", "") for x in v if isinstance(x, dict))
    return v if v is not None else ""


def fetch_all(tok):
    """全表分页读取，返回 fields dict 列表。单一实现：audit.py 也调用它（守卫R）。"""
    rows, page = [], ""
    while True:
        d = call("GET", f"{BASE}?page_size=500&page_token={urllib.parse.quote(page)}", tok)
        data = d.get("data", {})
        rows += [r.get("fields", {}) for r in data.get("items", [])]
        if not data.get("has_more"):
            break
        page = data.get("page_token", "")
    return rows


def ischild(f):
    """子记录判定：父记录字段带 record_ids 或非空 text_arr。"""
    pv = f.get("父记录")
    if isinstance(pv, list):
        for it in pv:
            if isinstance(it, dict) and (it.get("record_ids") or it.get("text_arr")):
                return True
    return False


def progress_lines(rows):
    """批量进度读数。口径（9/15 逸凡确认）：每条记录算一份，父/子各算一份，不折叠。"""
    kids = {id(f) for f in rows if ischild(f)}
    tot, nkid = len(rows), len(kids)

    def brk(lst):
        k = sum(1 for x in lst if id(x) in kids)
        return f"顶层{len(lst) - k}+子{k}"

    conf = [f for f in rows if f.get("地址复核") is True]
    ship = [f for f in rows if f.get("已邮寄/交付") is True]
    pack = [f for f in rows if f.get("已打包") is True]
    num = [f for f in rows if str(g(f, "邮寄编号") or "").strip()]
    return [
        f"总记录 {tot} | 顶层(父/独立) {tot - nkid} | 子记录 {nkid}",
        f"批量进度: 地址复核确认 {len(conf)}({brk(conf)})"
        f" | 已邮寄/交付 {len(ship)}({brk(ship)})"
        f" | 已打包 {len(pack)}({brk(pack)})"
        f" | 有邮寄编号 {len(num)}({brk(num)})",
    ]


def after_write(tok, resp):
    """写入成功后自动附两个实时读数（9/18 逸凡硬规则 + 9/17 B3「先写后读」）。
    目的：让回执里的数字必然来自「写完之后」的读数，杜绝陈旧数字（9/19 序号172 案例）。"""
    if not isinstance(resp, dict) or resp.get("code") != 0:
        return
    if os.environ.get("CFO_SKIP_PROGRESS") == "1":
        return
    try:
        for l in progress_lines(fetch_all(tok)):
            print(l)
    except Exception as e:
        print(f"!! 进度读数失败: {e}")


def warn_format(fields):
    """写入前的字段格式两道校验（编译进默认路径，不依赖人记）：
    ① 收件信息首段必须是实际签收人，不是「名字」列的值（2026-09-14 血泪规则）。
    ② 名字列只写名字，身份/关系/职级注释（括号）另置公司列或备注（2026-09-11 字段规则，
       2026-09-16 序号 342 因未编译此条再次违反）。"""
    info = fields.get("收件信息")
    name = fields.get("名字")

    def _norm(x):
        return re.sub(r"\s+", "", str(x)).casefold()

    if isinstance(info, str) and isinstance(name, str) and name.strip():
        segs = info.split()
        # 2026-09-18 修正：比较前归一化（去空白 + 大小写不敏感）。
        # 反例：序号 360 名字 Clary / 首段 clary，原大小写敏感比较漏报。
        if segs and _norm(segs[0]) == _norm(name):
            print("!! 格式告警：收件信息首段与「名字」列相同。首段须为实际签收人，"
                  "名字列只写名字（2026-09-14 逸凡纠正）。")
    if isinstance(name, str) and any(ch in name for ch in ("（", "）", "(", ")")):
        print("!! 格式告警：名字列含括号注释。名字列只写名字，"
              "身份/关系/职级说明请放公司列或备注（2026-09-11 字段规则）。")


def main():
    cmd = sys.argv[1]
    tok = token()
    if cmd == "create":
        payload = json.loads(sys.argv[2])
        warn_format(payload)
        r = call("POST", BASE, tok, {"fields": payload})
        print(json.dumps(r, ensure_ascii=False, indent=1))
        after_write(tok, r)
    elif cmd == "update":
        rid = sys.argv[2]
        cur = call("GET", f"{BASE}/{rid}", tok)
        cf = (cur.get("data", {}).get("record", {}) or {}).get("fields", {})
        print("[update 前原值] " + rid + " | "
              + " | ".join(f"{k}:{g(cf, k)}" for k in ("序号", "名字", "收件信息")))
        payload = json.loads(sys.argv[3])
        warn_format(payload)
        r = call("PUT", f"{BASE}/{rid}", tok, {"fields": payload})
        print(json.dumps(r, ensure_ascii=False, indent=1))
        after_write(tok, r)
    elif cmd == "get":
        r = call("GET", f"{BASE}/{sys.argv[2]}", tok)
        print(json.dumps(r, ensure_ascii=False, indent=1))
    elif cmd == "progress":
        # 独立读数命令（不想写入、只想要两个数字时用；等价于 audit 的进度行）
        for l in progress_lines(fetch_all(tok)):
            print(l)
    elif cmd in ("find", "findmany"):
        rows = []
        if cmd == "findmany":
            page = ""
            while True:
                d = call("GET", f"{BASE}?page_size=500&page_token={urllib.parse.quote(page)}", tok)
                data = d.get("data", {})
                rows += data.get("items", [])
                if not data.get("has_more"):
                    break
                page = data.get("page_token", "")
        for kw in sys.argv[2:]:
            if cmd == "findmany":
                print(f"=== {kw} ===")
            n = 0
            if cmd == "find":
                page = ""
                while True:
                    d = call("GET", f"{BASE}?page_size=500&page_token={urllib.parse.quote(page)}", tok)
                    data = d.get("data", {})
                    rows += data.get("items", [])
                    if not data.get("has_more"):
                        break
                    page = data.get("page_token", "")
            for r in rows:
                f = r.get("fields", {})
                blob = " ".join(str(g(f, k)) for k in ("名字", "公司", "收件信息", "序号"))
                if kw in blob:
                    n += 1
                    print(f"  {r['record_id']} | 序号{g(f,'序号')} | {g(f,'名字')} | {g(f,'公司')}"
                          f" | 分类={g(f,'分类')} | {g(f,'收件信息')} | 复核={f.get('地址复核')}")
            print("命中", n)


if __name__ == "__main__":
    main()
