#!/usr/bin/env python3
"""pending 保鲜检查 —— Dreaming Step 0 第一条命令。

规则来源：pending-ceo.json purpose 段（2026-10-24 立：每项必须带 last_verified_at，
引用前校验 <=24h，超时当场重跑读数）。

为什么要脚本：该规则在说明段里挂了 5 天，三项读数过期 1-5 天无人发现。
规则生效 = 自动加载路径 × 决策点绑定，缺一即失效（守卫七）。

用法：
    python3 memory/pending-freshness.py            # 输出表 + STALE 计数
    python3 memory/pending-freshness.py --strict   # 有 STALE 则 exit 1
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
PENDING = BASE / "pending-ceo.json"
TZ = timezone(timedelta(hours=8))
MAX_AGE_HOURS = 24

def parse(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None

def main():
    strict = "--strict" in sys.argv
    data = json.loads(PENDING.read_text(encoding="utf-8"))
    now = datetime.now(TZ)
    stale, missing = [], []
    print(f"pending 保鲜检查 @ {now.strftime('%Y-%m-%d %H:%M')} (UTC+8)")
    print(f"{'id':32} {'状态':16} {'最后校验':20} {'龄期':>6}  验证层")
    print("-" * 96)
    for it in data.get("items", []):
        iid = it.get("id", "?")
        status = it.get("状态", "?")
        ts = parse(it.get("last_verified_at"))
        layer = it.get("验证层", "-")
        # 只校验未结项：done 项的读数是历史证据，不要求保鲜
        if status == "done":
            hours = (now - ts).total_seconds() / 3600 if ts else 0
            print(f"{iid:32} {status:16} {(it.get('last_verified_at') or '-'):20} {f'{hours:.0f}h':>6}  {layer}")
            continue
        if ts is None:
            missing.append(iid)
            age = "无读数"
            mark = "MISSING"
        else:
            hours = (now - ts).total_seconds() / 3600
            age = f"{hours:.0f}h"
            mark = "STALE" if hours > MAX_AGE_HOURS else ""
            if mark and status != "done":
                stale.append((iid, hours))
        print(f"{iid:32} {status:16} {(it.get('last_verified_at') or '-'):20} {age:>6}  {layer} {mark}")
    print("-" * 96)
    open_items = [i for i in data.get("items", []) if i.get("状态") != "done"]
    print(f"总数 {len(data.get('items', []))} / 未结 {len(open_items)} / STALE {len(stale)} / 缺读数 {len(missing)}")
    if stale:
        print("需当场重跑读数的项：" + ", ".join(f"{i}({h:.0f}h)" for i, h in stale))
    if missing:
        print("缺 last_verified_at：" + ", ".join(missing))
    if strict and (stale or missing):
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
