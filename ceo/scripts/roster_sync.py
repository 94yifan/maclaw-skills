#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
roster_sync.py v3 — 从飞书人事（标准版 ehr v1, view=full）重建在职名册

关键点：
  1. 必须带 view=full，否则接口只返回 system_fields 基础四字段（姓名/工号/类型/状态），
     拿不到入职日期与出生日期。
  2. view=full 会同时返回身份证号、银行卡、社保公积金、户口等极高敏字段。
     本脚本只按白名单提取 7 个字段，其余一律不落地、不写文件、不打印。
     白名单：name / employee_no / employee_type / status / hire_date / birthday / job.name / department_id
  3. 在职口径：status 2（试用/在职）+ 3（正式）；5=已离职，不取。

输出：
  roster_data.json  在职名册，字段缺省即 data_unavailable，不猜测、不回填旧表
  roster_meta.json  来源 / 人数 / 覆盖率 / 时间 / 失败原因
退出码：0 成功，2 失败（保留上次文件不动）
"""
import json, os, sys, urllib.request, urllib.error, datetime, shutil

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.expanduser("~/.openclaw/openclaw.json")
ROSTER = os.path.join(WS, "roster_data.json")
META = os.path.join(WS, "roster_meta.json")
BACKUP_DIR = os.path.join(WS, "backups")
VERBOSE = "--verbose" in sys.argv
LIVE_STATUS = (2,)  # 2=在职；3=已离职（实测：status=3 的 14 人全部不在通讯录），5=历史离职
WHITELIST = ("name", "employee_no", "employee_type", "status", "hire_date", "birthday",
             "department_id", "conversion_date", "probation_months", "employee_form_status")


def log(*a):
    if VERBOSE:
        print(*a)


def call(url, tok=None, data=None):
    h = {"Content-Type": "application/json"}
    if tok:
        h["Authorization"] = "Bearer " + tok
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=h)
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"code": e.code, "msg": "http error"}


def token():
    f = json.load(open(CONF))["channels"]["feishu"]
    r = call("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
             data={"app_id": f["appId"], "app_secret": f["appSecret"]})
    if r.get("code") != 0:
        raise RuntimeError("token: %s" % r)
    return r["tenant_access_token"]


def count_contact_users(tok):
    depts, stack = set(), ["0"]
    while stack:
        p = stack.pop(); page = ""
        while True:
            u = ("https://open.feishu.cn/open-apis/contact/v3/departments?parent_department_id=%s"
                 "&page_size=50&department_id_type=open_department_id" % p)
            if page: u += "&page_token=" + page
            d = (call(u, tok).get("data") or {})
            for it in d.get("items", []):
                depts.add(it["open_department_id"]); stack.append(it["open_department_id"])
            if not d.get("has_more"): break
            page = d.get("page_token", "")
    users = set()
    for did in list(depts) + ["0"]:
        page = ""
        while True:
            u = ("https://open.feishu.cn/open-apis/contact/v3/users/find_by_department?department_id=%s"
                 "&page_size=50&department_id_type=open_department_id&user_id_type=open_id" % did)
            if page: u += "&page_token=" + page
            d = (call(u, tok).get("data") or {})
            for it in d.get("items", []): users.add(it["open_id"])
            if not d.get("has_more"): break
            page = d.get("page_token", "")
    return len(users)


def fetch_live(tok):
    out = []
    for st in LIVE_STATUS:
        page = ""
        while True:
            u = "https://open.feishu.cn/open-apis/ehr/v1/employees?page_size=100&view=full&status=%d" % st
            if page:
                u += "&page_token=" + page
            r = call(u, tok)
            if r.get("code") != 0:
                return out, "ehr status=%d: %s %s" % (st, r.get("code"), r.get("msg"))
            d = r.get("data") or {}
            for it in d.get("items", []):
                sf = it.get("system_fields") or {}
                rec = {k: sf.get(k) for k in WHITELIST}          # 只取白名单
                job = sf.get("job") or {}
                rec["job_title"] = job.get("name", "") if isinstance(job, dict) else ""
                jl = sf.get("job_level") or {}
                rec["job_level"] = jl.get("name", "") if isinstance(jl, dict) else ""
                rec["open_id"] = it.get("user_id", "")
                out.append(rec)
            if not d.get("has_more"):
                break
            page = d.get("page_token", "")
    return out, None


def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    global tok_global
    try:
        tok_global = token()
        live, err = fetch_live(tok_global)
    except Exception as e:
        live, err = [], "exception: %s" % e
    log("live:", len(live), "err:", err)

    if not live:
        old = json.load(open(ROSTER)) if os.path.exists(ROSTER) else []
        json.dump({"source": "ehr", "status": "failed", "count": len(old),
                   "synced_at": now, "error": err or "ehr 在职名单为空"},
                  open(META, "w"), ensure_ascii=False, indent=2)
        log("FAILED")
        return 2

    rows = []
    for p in live:
        if not p.get("name") or p["name"] == "测试":
            continue
        rows.append({
            "name": p["name"],
            "employee_no": p.get("employee_no", ""),
            "title": p.get("job_title", ""),
            "entry_date": p.get("hire_date") or "",
            "birthday": p.get("birthday") or "",
            "employee_type": p.get("employee_type"),
            "status": p.get("status"),
            "department_id": p.get("department_id", ""),
            "open_id": p.get("open_id", ""),
            "job_level": p.get("job_level", ""),
            "conversion_date": p.get("conversion_date") or "",
            "probation_months": p.get("probation_months"),
            "employee_form_status": p.get("employee_form_status"),
            "sources": {"base": "ehr", "birth": "ehr" if p.get("birthday") else None,
                        "entry": "ehr" if p.get("hire_date") else None},
        })

    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists(ROSTER):
        shutil.copy2(ROSTER, os.path.join(BACKUP_DIR, "roster_data.%s.json"
                                          % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    json.dump(rows, open(ROSTER, "w"), ensure_ascii=False, indent=2)
    nb = sum(1 for r in rows if r["birthday"])
    ne = sum(1 for r in rows if r["entry_date"])
    nt = sum(1 for r in rows if r["title"])
    # 交叉校验：在职人数应与通讯录可见成员数一致
    contact_n = None
    try:
        contact_n = count_contact_users(tok_global)
    except Exception as e:
        log("contact crosscheck failed:", e)
    json.dump({"source": "ehr_full", "status": "ok", "count": len(rows), "synced_at": now,
               "birthday_covered": nb, "entry_covered": ne, "title_covered": nt,
               "contact_crosscheck": contact_n,
               "crosscheck_ok": (contact_n == len(rows)) if contact_n else None,
               "error": err}, open(META, "w"), ensure_ascii=False, indent=2)
    log("written", len(rows), "birthday", nb, "entry", ne, "title", nt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
