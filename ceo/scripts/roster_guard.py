#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
roster_guard.py — 名册消费前的准入校验（2026-10-30 立）

为什么存在：
  生日 / 入职周年 / 转正提醒读的是 roster_data.json 这份静态快照。
  10-30 查出错发 6 人次、漏报 3 名新员工的根因就一条：
  消费者（提醒 job）从不校验它读的名单是不是「在职」且「够新」。
  本脚本把这件事变成一次可判定的读数，不通过就拒绝消费。

校验四件（缺一即 FAIL）：
  1. 文件存在、可解析、非空 list
  2. 每条 status == 2（在职唯一口径）；出现 3 / 5 即视为名单混入离职人员
  3. synced_at 距今 ≤ MAX_AGE_H（默认 25h），08:00 的 job 最坏吃到前一日 15:30 的快照
  4. meta.count == len(records)，crosscheck_ok 为 true，birthday / entry 覆盖率 == count

用法：
  python3 scripts/roster_guard.py            # 打印一行结论，exit 0 通过 / 2 不通过
  python3 scripts/roster_guard.py --json     # 机器可读

设计纪律（守卫十七补）：本脚本只报「已校验到哪一层」，不报「已修好」。
"""
import json, os, sys, datetime

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(WS, "roster_data.json")
META = os.path.join(WS, "roster_meta.json")
MAX_AGE_H = 25
LIVE_STATUS = 2


def fail(code, msg, extra=None):
    line = f"FAIL {code} | {msg}"
    if extra:
        line += f" | {extra}"
    print(line)
    if "--json" in sys.argv:
        print(json.dumps({"ok": False, "code": code, "msg": msg, "extra": extra}, ensure_ascii=False))
    sys.exit(2)


def main():
    if not os.path.exists(ROSTER):
        fail("E_MISSING", "roster_data.json 不存在")
    if os.path.getsize(ROSTER) < 200:
        fail("E_EMPTY", f"roster_data.json 仅 {os.path.getsize(ROSTER)}B，疑似占位文件")

    try:
        recs = json.load(open(ROSTER, encoding="utf-8"))
    except Exception as e:
        fail("E_PARSE", f"JSON 解析失败: {e}")
    if not isinstance(recs, list) or not recs:
        fail("E_SHAPE", f"顶层应为非空 list，实际 {type(recs).__name__}")

    # 2. 状态口径
    bad = [r for r in recs if r.get("status") != LIVE_STATUS]
    if bad:
        names = "、".join(r.get("name", "?") for r in bad[:8])
        fail("E_STATUS", f"{len(bad)}/{len(recs)} 条非在职口径(status!=2)", names)

    # 3. 时效
    if not os.path.exists(META):
        fail("E_NO_META", "roster_meta.json 不存在，无法判定时效")
    meta = json.load(open(META, encoding="utf-8"))
    ts = meta.get("synced_at", "")
    try:
        synced = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except Exception:
        fail("E_META_TS", f"synced_at 不可解析: {ts!r}")
    age_h = (datetime.datetime.now() - synced).total_seconds() / 3600
    if age_h > MAX_AGE_H:
        fail("E_STALE", f"快照龄 {age_h:.1f}h 超过 {MAX_AGE_H}h，先跑 scripts/roster_sync.py")

    # 4. 一致性
    if meta.get("status") != "ok":
        fail("E_SYNC_STATUS", f"上次同步 status={meta.get('status')} error={meta.get('error')}")
    if meta.get("count") != len(recs):
        fail("E_COUNT", f"meta.count={meta.get('count')} 与记录数 {len(recs)} 不一致")
    if not meta.get("crosscheck_ok"):
        fail("E_XCHECK", "与通讯录交叉校验未通过")
    for f in ("birthday_covered", "entry_covered"):
        if meta.get(f) != len(recs):
            fail("E_COVER", f"{f}={meta.get(f)} != {len(recs)}")

    print(f"PASS 在职 {len(recs)} 人 | 快照龄 {age_h:.1f}h | 生日/入职覆盖 100% | "
          f"口径 status=2 | synced_at {ts}")


if __name__ == "__main__":
    main()
