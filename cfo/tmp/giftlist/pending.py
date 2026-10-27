#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""未闭环清单输出器（守卫AJ）。

用法:
  python3 pending.py          # 摘要：各优先级计数 + 置顶项
  python3 pending.py --all    # 全量列出

规则（守卫AJ）：本清单不再例行推送。仅 ① 每周一落盘；② 某条阻碍当天动作时即时问；
③ 逸凡主动询问时用本脚本一次性输出。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pending.json")


def load():
    with open(SRC, encoding="utf-8") as f:
        return json.load(f)



def add_item(argv):
    """--add id|priority|item|default_action|need  （守卫BD：待办只认 pending.json 一个来源）

    守卫AY：写入前校验必填项与 id 格式，非法即拒绝，不静默采用。
    """
    import datetime
    args = [a for a in argv[1:] if a != "--add"]
    if len(args) != 5:
        print("用法: pending.py --add <id> <priority> <item> <default_action> <need>", file=sys.stderr)
        return 2
    pid, prio, item, act, need = (a.strip() for a in args)
    if not re.fullmatch(r"[a-z0-9-]{3,40}", pid):
        print(f"FAIL: id 非法 {pid!r}（只容许小写字母/数字/连字符，3-40 位）", file=sys.stderr)
        return 2
    if prio not in ("置顶", "高", "中", "低", "P2"):
        print(f"FAIL: priority 非法 {prio!r}（置顶/高/中/低/P2）", file=sys.stderr)
        return 2
    data = load()
    for i in data["items"]:
        if i["id"] == pid:
            i.update({"priority": prio, "item": item, "default_action": act, "need": need,
                      "status": "open", "updated": datetime.datetime.now().strftime("%Y-%m-%d")})
            data["updated"] = datetime.date.today().isoformat()
            open(SRC, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
            print(f"UPDATED {pid} [{prio}]")
            return 0
    data["items"].append({"id": pid, "priority": prio, "item": item, "default_action": act,
                          "need": need, "status": "open",
                          "added": datetime.date.today().isoformat()})
    data["updated"] = datetime.date.today().isoformat()
    open(SRC, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
    open_ = len([i for i in data["items"] if i.get("status") == "open"])
    print(f"ADDED {pid} [{prio}] open={open_}")
    return 0


def main():
    if "--add" in sys.argv:
        raise SystemExit(add_item(sys.argv))
    data = load()
    items = [i for i in data.get("items", []) if i.get("status") == "open"]
    show_all = "--all" in sys.argv
    print(f"未闭环清单（更新 {data.get('updated','?')}，open {len(items)} 条）")
    if show_all:
        for i in items:
            print(f"  [{i.get('priority','?')}] {i['id']}: {i['item']}")
            print(f"        → 默认动作: {i.get('default_action','-')}（{i.get('need','-')}）")
    else:
        from collections import Counter
        c = Counter(i.get("priority", "?") for i in items)
        print("  优先级: " + " / ".join(f"{k} {v}" for k, v in c.items()))
        for i in items:
            if i.get("priority") in ("置顶", "高"):
                print(f"  [{i['priority']}] {i['item']} → {i.get('default_action','-')}")


if __name__ == "__main__":
    main()
