#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""当日交互判定单入口（守卫BB：一个数只有一个来源；守卫AM：不得默认零交互）

输出一行 DAY-PROBE 结论 + sessions 清单。
所有路径用 pathlib 判存在，不依赖 cat/ls 的退出码 —— 10/29 的诊断 warn 就是
链式命令里 cat 一个不存在的 memory 文件把整条命令传染成 failed。
用法: python3 day_probe.py [YYYY-MM-DD]
"""
import sys
from datetime import date, datetime
from pathlib import Path

SESS = Path.home() / ".openclaw" / "agents" / "cfo" / "sessions"
MEM = Path(__file__).resolve().parents[2] / "memory"


def main() -> int:
    if len(sys.argv) > 1:
        try:
            today = date.fromisoformat(sys.argv[1])
        except ValueError:
            print(f"WARN: 非法日期 {sys.argv[1]!r}，回落本机当日", file=sys.stderr)
            today = date.today()
    else:
        today = date.today()
    key = today.isoformat()

    # 同一 session 可能有多个分片/轮转文件，按 id 去重取最大体积
    seen = {}
    if SESS.is_dir():
        for p in sorted(SESS.glob("*.jsonl")):
            try:
                st = p.stat()
                m = datetime.fromtimestamp(st.st_mtime).date()
            except OSError:
                continue
            if m == today:
                sid = p.stem.split(".")[0][:8]
                seen[sid] = max(seen.get(sid, 0), st.st_size)
    hits = sorted(seen.items())
    memfile = MEM / f"{key}.md"
    mems = "exists" if memfile.exists() else "missing"

    # 判定：除本轮 dreaming 会话外还有别的会话 = 有交互；
    # 无 memory 日文件是弱证据，仅作参考（守卫AM）
    human = len(hits) > 1
    verdict = "有交互" if human else "零交互"
    print(f"DAY-PROBE {key} | sessions={len(hits)} | memory={mems} | verdict={verdict}")
    for sid, size in hits:
        print(f"  session {sid} {size}B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
