#!/usr/bin/env python3
"""
SC raw JSON 应急信号提取脚本（2026-08-11 固化）
用法: python3 scripts/sc-raw-signal-extract.py [--json /tmp/tea-raw-2026-06-14.json] [--brands 5] [--chars 180]
说明:
- SC 日报格式化断链时（硬编码路径问题），直接读 raw JSON 提取品牌信号
- 文件名日期不可信，mtime 才是新鲜度依据
- 输出: 每个品牌最新 N 条帖子摘要（时间+前 N 字符）
"""
import json
import os
import sys
import argparse

DEFAULT_JSON = "/tmp/tea-raw-2026-06-14.json"

def main():
    parser = argparse.ArgumentParser(description="SC raw JSON 应急信号提取")
    parser.add_argument("--json", default=DEFAULT_JSON, help="raw JSON 路径")
    parser.add_argument("--brands", type=int, default=5, help="每品牌输出帖子数")
    parser.add_argument("--chars", type=int, default=180, help="每条帖子截取字符数")
    args = parser.parse_args()

    if not os.path.exists(args.json):
        print(f"错误: {args.json} 不存在")
        sys.exit(1)

    mtime = os.path.getmtime(args.json)
    import datetime
    mt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    print(f"# raw JSON: {args.json} (mtime {mt})")

    with open(args.json) as f:
        data = json.load(f)

    print(f"品牌数: {len(data)}")
    for brand, posts in data.items():
        if not posts:
            print(f"===== {brand} (空) =====")
            continue
        recent = posts[:args.brands]
        print(f"===== {brand} ({len(posts)}条) =====")
        for p in recent:
            t = p.get("text", "").replace("\n", " ")[:args.chars]
            tm = p.get("time", "")
            print(f"  [{tm}] {t}")
        print()

if __name__ == "__main__":
    main()
