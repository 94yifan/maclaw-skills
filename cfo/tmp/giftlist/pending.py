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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pending.json")


def load():
    with open(SRC, encoding="utf-8") as f:
        return json.load(f)


def main():
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
